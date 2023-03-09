import { sendUnaryData, ServerUnaryCall, status } from 'grpc'
import { AdminChannelId, AnnounceMessagesResponse, EmptyMessage, SaveMessageRequest, SetAnnounceMessageRequest, SetAnnounceMessagesRequest } from '../grpc/sub-unsub_pb'
import { prisma } from '../util/prisma-factory'

export const setJoinLeftMessage =
    async (req: ServerUnaryCall<SetAnnounceMessagesRequest>, callback: sendUnaryData<EmptyMessage>, messageType: string) => {
        const messages = req.request.getMessagesList();
        const adminChannelId = req.request.getAdminchannel();

        try {
            await prisma.$transaction(async prisma => {
                const adminChannel = await prisma.adminChannel
                    .findUnique({
                        include: {
                            announceBot: {
                                include: {
                                    botMessages: true
                                }
                            }
                        },
                        where: {
                            channelId: adminChannelId
                        }
                    });

                if (!adminChannel) {
                    throw new Error('ADMIN_CHANNEL_NOT_FOUND');
                }

                const announceBot = adminChannel.announceBot;

                if (!announceBot) {
                    throw new Error("ANNOUNCE_BOT_NOT_FOUND");
                }

                const existentMessages = announceBot
                    .botMessages
                    .filter(msg => msg.messageType == messageType);

                const newMessages = messages.map(msg => {
                    return {
                        messageId: msg.getMessageid(),
                        channelId: msg.getChannelid(),
                        messageType: messageType
                    }
                });

                await prisma.announceBot
                    .update({
                        where: {
                            id: announceBot.id
                        },
                        data: {
                            botMessages: {
                                deleteMany: {
                                    id: {
                                        in: existentMessages.map(m => m.id)
                                    }
                                },
                                createMany: {
                                    data: newMessages
                                }
                            }
                        }
                    })
            }, {
                isolationLevel: 'RepeatableRead'
            });

            callback(null, new EmptyMessage());
        } catch (e: any) {
            callback({
                message: e.message,
                name: e.message,
                code: status.INTERNAL
            },
                null);
        }
    }


export const getJoinLeftMessage =
    async (req: ServerUnaryCall<AdminChannelId>, callback: sendUnaryData<AnnounceMessagesResponse>, messageType: string) => {
        const adminChannelId = req.request.getChannelid();

        try {
            const messages = await prisma.$transaction(async prisma => {
                const adminChannel = await prisma.adminChannel
                    .findUnique({
                        include: {
                            announceBot: {
                                include: {
                                    botMessages: {
                                        orderBy: {
                                            id: 'asc'
                                        }
                                    }
                                }
                            }
                        },
                        where: {
                            channelId: adminChannelId
                        }
                    });

                if (!adminChannel) {
                    throw new Error('ADMIN_CHANNEL_NOT_FOUND');
                }

                const announceBot = adminChannel.announceBot;

                if (!announceBot) {
                    throw new Error("ANNOUNCE_BOT_NOT_FOUND");
                }

                const messages = announceBot
                    .botMessages
                    .filter(msg => msg.messageType == messageType);

                return messages;
            }, {
                isolationLevel: 'ReadCommitted'
            });

            const response = new AnnounceMessagesResponse();
            response.setMessagesList(messages.map(msg => {
                const body = new SaveMessageRequest();
                body.setChannelid(msg.channelId);
                body.setMessageid(msg.messageId);
                return body;
            }));

            callback(null, response);
        } catch (e: any) {
            callback({
                message: e.message,
                name: e.message,
                code: status.INTERNAL
            },
                null);
        }
    }