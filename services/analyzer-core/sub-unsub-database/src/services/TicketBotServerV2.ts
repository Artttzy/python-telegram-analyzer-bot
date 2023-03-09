import { handleUnaryCall, sendUnaryData, ServerUnaryCall, status } from "grpc";
import { ITicketsServer } from "../grpc/ticket-bot_grpc_pb";
import {
    AgentData,
    AnnouneBotExists,
    BoolWrapper,
    CallcenterData,
    ChannelId,
    CheckAvailableAgentsRequest,
    CloseTicketRequest,
    EditAgentRequest,
    Empty,
    GetStatusRequest,
    OpenTicketRequest,
    RegisterCallcenterRequest,
    SupportState,
    SupportStatus,
    TicketData,
    TicketIdRequest,
    TicketUpdateResponse,
    UserMessageRequest,
    UserState,
    WorkdayData,
} from "../grpc/ticket-bot_pb";
import { prisma } from '../util/prisma-factory'
import { getWorkday, setWorkday } from "../util/workday";


export class TicketBotServerV2 implements ITicketsServer {
    openTicket: handleUnaryCall<OpenTicketRequest, TicketData> =
        async (req: ServerUnaryCall<OpenTicketRequest>, callback: sendUnaryData<TicketData>) => {
            const userId = req.request.getUserid();
            const callcenterId = req.request.getCallcenterid();
            const channelId = req.request.getChannelid();
            const username = req.request.getUsername();

            try {
                const ticket = await prisma.$transaction(async (tx) => {
                    const callcenter = await tx.callCenter
                        .findUnique({
                            include: {
                                agents: {
                                    include: {
                                        activeTicket: true
                                    }
                                },
                                channel: true
                            },
                            where: {
                                externalId: callcenterId
                            }
                        });

                    if (!callcenter) {
                        throw new Error('CALLCENTER_NOT_FOUND');
                    }

                    if (callcenter.channel.channelId !== channelId) {
                        throw new Error('BAD_CHANNEL_ID');
                    }

                    const latestTicket = await prisma.supportTicket.findFirst({
                        where: {
                            callCenterKey: callcenter.id,
                            userId: userId
                        },
                        orderBy: {
                            openTime: 'desc'
                        }
                    });

                    if (latestTicket) {
                        const timeNow = new Date();
                        if (timeNow.getTime() - latestTicket.openTime.getTime() < 2 * 60 * 60 * 1000) {
                            throw new Error('TOO_MANY_TICKETS');
                        }
                    }

                    const createdTicket = await tx.supportTicket.create({
                        data: {
                            userId: userId,
                            openTime: new Date(),
                            findTime: null,
                            status: 'open',
                            agentKey: null,
                            callCenterKey: callcenter.id,
                            username: username
                        }
                    });

                    return {
                        ticket: createdTicket,
                        agent: null
                    };
                },
                    {
                        isolationLevel: 'RepeatableRead'
                    }
                );

                const response = new TicketData();
                response.setTicketid(ticket.ticket.id);
                response.setUsermessages(ticket.ticket.userMessages);
                response.setAgentmessages(ticket.ticket.agentMessages);
                response.setUserid(ticket.ticket.userId);
                response.setEmpty(new Empty());
                response.setUsername(ticket.ticket.username ?? '');

                callback(null, response);
            }
            catch (e: any) {
                switch (e.message) {
                    case 'CALLCENTER_NOT_FOUND':
                        callback({
                            code: status.INTERNAL,
                            name: 'CALLCENTER_NOT_FOUND',
                            message: 'CALLCENTER_NOT_FOUND'
                        },
                            null
                        );
                        break;

                    case 'BAD_CHANNEL_ID':
                        callback({
                            code: status.INVALID_ARGUMENT,
                            name: 'BAD_CHANNEL_ID',
                            message: 'BAD_CHANNEL_ID'
                        },
                            null
                        );
                        break;

                    case 'TICKET_ALREADY_OPENED':
                        callback({
                            code: status.INTERNAL,
                            name: 'TICKET_ALREADY_OPENED',
                            message: 'TICKET_ALREADY_OPENED'
                        },
                            null
                        );
                        break;

                    case 'TOO_MANY_TICKETS':
                        callback({
                            code: status.INTERNAL,
                            name: 'TOO_MANY_TICKETS',
                            message: 'TOO_MANY_TICKETS'
                        },
                            null
                        );
                        break;

                    default:
                        console.error(e);

                        callback({
                            code: status.INTERNAL,
                            name: 'UNKNOWN_ERROR',
                            message: 'Unknown error occured, please try again later'
                        },
                            null
                        );
                }
            }
        }

    getStatus: handleUnaryCall<GetStatusRequest, SupportStatus> =
        async (req: ServerUnaryCall<GetStatusRequest>,
            callback: sendUnaryData<SupportStatus>) => {

            const userId = req.request.getUserid();
            const callCenterId = req.request.getCallcenterid();

            const response = await prisma.$transaction(async tx => {
                const callcenter = await tx.callCenter
                    .findUnique({
                        where: {
                            externalId: callCenterId
                        }
                    });

                const agent = callcenter ? await tx.supportAgent
                    .findUnique({
                        include: {
                            callCenter: true
                        },
                        where: {
                            userId_callCenterKey: {
                                userId: userId,
                                callCenterKey: callcenter.id
                            }
                        }
                    }) : null;

                const response = new SupportStatus();

                if (agent) {
                    response.setUserstate(UserState.AGENT);
                    response.setSupportstate(SupportState.IDLE);
                    response.setEmpty(new Empty());
                    return response;
                } else {
                    return null;
                }
            }, {
                isolationLevel: 'ReadCommitted'
            });

            if (response) {
                callback(null, response);
            } else {
                callback({
                    code: status.INTERNAL,
                    name: 'INTERNAL',
                    message: 'INTERNAL'
                },
                    null
                );
            }
        }

    closeTicket: handleUnaryCall<CloseTicketRequest, TicketData> =
        async (req: ServerUnaryCall<CloseTicketRequest>,
            callback: sendUnaryData<TicketData>) => {
            const ticketId = req.request.getTicketid();

            try {
                const ticket = await prisma.$transaction(async tx => {
                    const ticket = await tx.supportTicket
                        .findUnique({
                            include: {
                                agent: true
                            },
                            where: {
                                id: ticketId
                            }
                        });

                    if (!ticket) {
                        throw new Error('TICKET_NOT_FOUND');
                    }

                    if (ticket.status === 'closed') {
                        throw new Error('ALREADY_CLOSED')
                    }

                    await tx.supportTicket
                        .update({
                            where: {
                                id: ticket.id
                            },
                            data: {
                                status: 'closed',
                                activeAgent: {
                                    disconnect: true
                                },
                                closeTime: new Date()
                            }
                        });

                    return ticket;
                }, {
                    isolationLevel: 'RepeatableRead'
                });

                const response = new TicketData();
                response.setUserid(ticket.userId.toString());
                response.setTicketid(ticket.id);
                response.setUsermessages(ticket.userMessages);
                response.setAgentmessages(ticket.agentMessages);
                response.setUsername(ticket.username ?? '');

                if (ticket.agent) {
                    response.setAgentid(ticket.agent.userId);
                } else {
                    response.setEmpty(new Empty());
                }

                callback(null, response);
            } catch (e: any) {
                switch (e.message) {
                    case 'TICKET_NOT_FOUND':
                        callback({
                            code: status.INTERNAL,
                            name: 'TICKET_NOT_FOUND',
                            message: 'TICKET_NOT_FOUND'
                        },
                            null
                        );
                        break;

                    case 'ALREADY_CLOSED':
                        callback({
                            code: status.INTERNAL,
                            name: 'ALREADY_CLOSED',
                            message: 'ALREADY_CLOSED'
                        },
                            null
                        );
                        break;

                    default:
                        console.error(e);

                        callback({
                            code: status.INTERNAL,
                            name: 'UNKNOWN_ERROR',
                            message: 'Unknown error occured, please try again later'
                        },
                            null
                        );
                }
            }
        }

    logAgentMessage: handleUnaryCall<TicketIdRequest, Empty> =
        async (req: ServerUnaryCall<TicketIdRequest>, callback: sendUnaryData<Empty>) => {
            const ticketId = req.request.getTicketid();

            await prisma.$transaction(async tx => {
                const ticket = await tx.supportTicket
                    .findUnique({
                        where: {
                            id: ticketId
                        }
                    });

                if (ticket /* && !ticket.answerTime */) {
                    await tx.supportTicket.update({
                        where: {
                            id: ticketId
                        },
                        data: {
                            answerTime: ticket.answerTime ? undefined : new Date(),
                            agentMessages: {
                                increment: 1
                            }
                        }
                    });
                }
            }, {
                isolationLevel: 'RepeatableRead'
            });

            callback(null, new Empty());
        }

    logUserMessage: handleUnaryCall<UserMessageRequest, BoolWrapper> =
        async (req: ServerUnaryCall<UserMessageRequest>,
            callback: sendUnaryData<BoolWrapper>) => {
            const ticketId = req.request.getTicketid();
            const messageId = req.request.getMessageid();

            const value = await prisma.$transaction(async prisma => {
                const ticket = await prisma.supportTicket
                    .findUnique({
                        where: {
                            id: ticketId
                        }
                    });

                if (ticket) {
                    const updated = await prisma.supportTicket.update({
                        where: {
                            id: ticket.id
                        },
                        data: {
                            userMessages: {
                                increment: 1
                            },
                            messages: {
                                create: {
                                    messageId: messageId
                                }
                            }
                        }
                    });

                    return updated.userMessages < 2;
                }

                return false;
            }, {
                isolationLevel: 'RepeatableRead'
            });

            const response = new BoolWrapper();
            response.setValue(value);
            callback(null, response);
        }


    checkAvailableAgents: handleUnaryCall<CheckAvailableAgentsRequest, TicketUpdateResponse> =
        async (req: ServerUnaryCall<CheckAvailableAgentsRequest>, callback: sendUnaryData<TicketUpdateResponse>) => {
            const callCenterId = req.request.getCallcenterid();

            const response = await prisma.$transaction(async tx => {
                const availableAgents = await tx.supportAgent
                    .findMany({
                        include: {
                            callCenter: true
                        },
                        where: {
                            activeTicketKey: null,
                            callCenter: {
                                externalId: callCenterId
                            },
                            isWorking: true
                        }
                    });

                const pendingTicket = await tx.supportTicket
                    .findFirst({
                        include: {
                            callCenter: true
                        },
                        orderBy: {
                            openTime: 'asc'
                        },
                        where: {
                            callCenter: {
                                externalId: callCenterId
                            },
                            status: 'open',
                            agent: null
                        }
                    });

                const response = new TicketUpdateResponse();

                if (availableAgents.length === 0 || !pendingTicket) {
                    response.setEmpty(new Empty());
                    return response;
                }

                const random = Math.floor(Math.random() * availableAgents.length);
                const agent = availableAgents[random];

                const updatedTicket = await tx.supportTicket
                    .update({
                        include: {
                            messages: {
                                orderBy: {
                                    id: 'asc'
                                }
                            }
                        },
                        where: {
                            id: pendingTicket.id
                        },
                        data: {
                            findTime: new Date(),
                            agentKey: agent.id //,
                            // activeAgent: {
                            //     connect: {
                            //         id: agent.id
                            //     }
                            // }
                        }
                    });

                const ticketData = new TicketData();
                console.log(ticketData)
                ticketData.setUserid(updatedTicket.userId);
                ticketData.setTicketid(updatedTicket.id);
                ticketData.setAgentid(agent.userId);
                ticketData.setUsermessages(updatedTicket.userMessages);
                ticketData.setAgentmessages(updatedTicket.agentMessages);
                ticketData.setUsername(updatedTicket.username ?? '');

                const messages = updatedTicket.messages
                    .map(msg => {
                        const mapped = new UserMessageRequest()
                        mapped.setTicketid(msg.ticketKey);
                        mapped.setMessageid(msg.messageId);
                        return mapped;
                    });

                response.setMessagesList(messages);
                response.setTicket(ticketData);
                return response;
            }, {
                isolationLevel: 'RepeatableRead'
            });

            callback(null, response);
        }

    registerCallcenter:
        handleUnaryCall<RegisterCallcenterRequest, CallcenterData> =
        async (req: ServerUnaryCall<RegisterCallcenterRequest>,
            callback: sendUnaryData<CallcenterData>) => {
            const cid = req.request.getChannelid();

            try {
                const response = await prisma
                    .$transaction(async tx => {
                        const channel = await tx
                            .adminChannel.findUnique({
                                where: {
                                    channelId: cid
                                }
                            });

                        if (!channel) {
                            throw new Error('CHANNEL_NOT_FOUND');
                        }

                        const callcenter = await tx
                            .callCenter.create({
                                include: {
                                    channel: true
                                },
                                data: {
                                    channelKey: channel.id
                                }
                            }).catch(() => {
                                throw new Error('UNABLE_TO_CRATE');
                            });

                        const response = new CallcenterData();
                        response.setChannelid(callcenter
                            .channel.channelId
                        );
                        response.setAgentsList([]);
                        response.setExternalid(callcenter.externalId);
                        return response;
                    }, {
                        isolationLevel: 'RepeatableRead'
                    });

                callback(null, response);
            } catch (e: any) {
                switch (e.message) {
                    case 'AGENT_NOT_FOUND':
                        callback({
                            code: status.INTERNAL,
                            name: 'AGENT_NOT_FOUND',
                            message: 'AGENT_NOT_FOUND'
                        },
                            null
                        );
                        break;

                    case 'CHANNEL_NOT_FOUND':
                        callback({
                            code: status.INTERNAL,
                            name: 'CHANNEL_NOT_FOUND',
                            message: 'CHANNEL_NOT_FOUND'
                        },
                            null
                        );
                        break;

                    case 'UNABLE_TO_CRATE':
                        callback({
                            code: status.INTERNAL,
                            name: 'UNABLE_TO_CRATE',
                            message: 'UNABLE_TO_CRATE'
                        },
                            null
                        );
                        break;

                    default:
                        console.error(e);

                        callback({
                            code: status.INTERNAL,
                            name: 'UNKNOWN_ERROR',
                            message: 'Unknown error occured, please try again later'
                        },
                            null
                        );
                }
            }
        }

    getCallcenterByChannelId:
        handleUnaryCall<ChannelId, CallcenterData> =
        async (req: ServerUnaryCall<ChannelId>,
            callback: sendUnaryData<CallcenterData>) => {
            const channelId = req.request.getChannelid();

            try {
                const response = await prisma
                    .$transaction(async prisma => {
                        const channel = await prisma
                            .adminChannel.findUnique({
                                include: {
                                    callCenters: {
                                        include: {
                                            agents: true
                                        }
                                    }
                                },
                                where: {
                                    channelId: channelId
                                }
                            });

                        if (!channel) {
                            throw new Error('CHANNEL_NOT_FOUND');
                        }

                        if (!channel.callCenters) {
                            throw new Error('CALLCENTER_NOT_FOUND');
                        }

                        const callcenter = channel.callCenters;
                        const response = new CallcenterData();
                        response.setExternalid(callcenter.externalId);
                        response.setChannelid(channel.channelId);

                        const agents = callcenter
                            .agents.map(a => {
                                const agent = new AgentData();
                                agent.setUserid(a.userId);
                                return agent;
                            });

                        response.setAgentsList(agents);
                        return response;
                    }, {
                        isolationLevel: 'ReadCommitted'
                    });

                callback(null, response);
            } catch (e: any) {
                switch (e.message) {
                    case 'CHANNEL_NOT_FOUND':
                        callback({
                            code: status.INTERNAL,
                            name: 'CHANNEL_NOT_FOUND',
                            message: 'CHANNEL_NOT_FOUND'
                        },
                            null
                        );
                        break;

                    case 'CALLCENTER_NOT_FOUND':
                        callback({
                            code: status.INTERNAL,
                            name: 'CALLCENTER_NOT_FOUND',
                            message: 'CALLCENTER_NOT_FOUND'
                        },
                            null
                        );
                        break;

                    default:
                        console.error(e);

                        callback({
                            code: status.INTERNAL,
                            name: 'UNKNOWN_ERROR',
                            message: 'Unknown error occured, please try again later'
                        },
                            null
                        );
                }
            }
        }

    removeCallCenter: handleUnaryCall<ChannelId, Empty> =
        async (req: ServerUnaryCall<ChannelId>,
            callback: sendUnaryData<Empty>) => {
            const channelId = req.request.getChannelid();

            try {
                await prisma.$transaction(async prisma => {
                    await prisma.adminChannel
                        .update({
                            where: {
                                channelId: channelId
                            },
                            data: {
                                callCenters: {
                                    delete: true
                                }
                            }
                        }).catch((e: any) => {
                            throw new Error('CALLCENTER_NOT_FOUND')
                        });
                }, {
                    isolationLevel: 'RepeatableRead'
                });

                callback(null, new Empty());
            } catch (e: any) {
                callback({
                    name: e.message,
                    message: e.message,
                    code: status.INTERNAL
                },
                    null
                );
            }
        }

    addAgent: handleUnaryCall<EditAgentRequest, CallcenterData> =
        async (req: ServerUnaryCall<EditAgentRequest>,
            callback: sendUnaryData<CallcenterData>) => {
            const userId = req.request.getAgent()!.getUserid();
            const channelId = req.request.getChannel()!.getChannelid();

            try {
                const response = await prisma
                    .$transaction(async prisma => {
                        const channel = await prisma
                            .adminChannel.findUnique({
                                include: {
                                    callCenters: true
                                },
                                where: {
                                    channelId: channelId
                                }
                            });

                        if (!channel) {
                            throw new Error('CHANNEL_NOT_FOUND');
                        }

                        if (!channel.callCenters) {
                            throw new Error('CALLCENTER_NOT_FOUND');
                        }

                        const callcenter = await prisma.callCenter
                            .update({
                                include: {
                                    agents: true
                                },
                                where: {
                                    id: channel.callCenters.id
                                },
                                data: {
                                    agents: {
                                        create: {
                                            userId: userId
                                        }
                                    }
                                }
                            }).catch((e: any) => {
                                throw new Error('ALREADY_ADDED');
                            });

                        const response = new CallcenterData();
                        response.setExternalid(callcenter.externalId);
                        response.setChannelid(channel.channelId);

                        const agents = callcenter
                            .agents.map(a => {
                                const agent = new AgentData();
                                agent.setUserid(a.userId);
                                return agent;
                            });

                        response.setAgentsList(agents);
                        return response;
                    }, {
                        isolationLevel: 'RepeatableRead'
                    });

                callback(null, response);
            } catch (e: any) {
                switch (e.message) {
                    case 'CHANNEL_NOT_FOUND':
                        callback({
                            code: status.INTERNAL,
                            name: 'CHANNEL_NOT_FOUND',
                            message: 'CHANNEL_NOT_FOUND'
                        },
                            null
                        );
                        break;

                    case 'CALLCENTER_NOT_FOUND':
                        callback({
                            code: status.INTERNAL,
                            name: 'CALLCENTER_NOT_FOUND',
                            message: 'CALLCENTER_NOT_FOUND'
                        },
                            null
                        )
                        break;

                    case 'ALREADY_ADDED':
                        callback({
                            code: status.INTERNAL,
                            name: 'ALREADY_ADDED',
                            message: 'ALREADY_ADDED'
                        },
                            null
                        )
                        break;

                    default:
                        console.error(e);

                        callback({
                            code: status.INTERNAL,
                            name: 'UNKNOWN_ERROR',
                            message: 'Unknown error occured, please try again later'
                        },
                            null
                        );
                }
            }
        }

    removeAgent: handleUnaryCall<EditAgentRequest, CallcenterData> =
        async (req: ServerUnaryCall<EditAgentRequest>,
            callback: sendUnaryData<CallcenterData>) => {
            const channelId = req.request.getChannel()!.getChannelid();
            const userId = req.request.getAgent()!.getUserid();

            try {
                const response = await prisma
                    .$transaction(async prisma => {
                        const channel = await prisma
                            .adminChannel.findUnique({
                                include: {
                                    callCenters: true
                                },
                                where: {
                                    channelId: channelId
                                }
                            });

                        if (!channel) {
                            throw new Error('CHANNEL_NOT_FOUND');
                        }

                        if (!channel.callCenters) {
                            throw new Error('CALLCENTER_NOT_FOUND');
                        }

                        const callcenter = await prisma.callCenter
                            .update({
                                include: {
                                    agents: true
                                },
                                where: {
                                    id: channel.callCenters.id
                                },
                                data: {
                                    agents: {
                                        delete: {
                                            userId_callCenterKey: {
                                                callCenterKey: channel.callCenters.id,
                                                userId: userId
                                            }
                                        }
                                    }
                                }
                            }).catch((e: any) => {
                                throw new Error('AGENT_NOT_FOUND');
                            });

                        const response = new CallcenterData();
                        response.setExternalid(callcenter.externalId);
                        response.setChannelid(channel.channelId);

                        const agents = callcenter
                            .agents.map(a => {
                                const agent = new AgentData();
                                agent.setUserid(a.userId);
                                return agent;
                            });

                        response.setAgentsList(agents);
                        return response;
                    }, {
                        isolationLevel: 'RepeatableRead'
                    });

                callback(null, response);
            } catch (e: any) {
                switch (e.message) {
                    case 'AGENT_NOT_FOUND':
                        callback({
                            code: status.INTERNAL,
                            name: 'AGENT_NOT_FOUND',
                            message: 'AGENT_NOT_FOUND'
                        },
                            null
                        );
                        break;

                    case 'CHANNEL_NOT_FOUND':
                        callback({
                            code: status.INTERNAL,
                            name: 'CHANNEL_NOT_FOUND',
                            message: 'CHANNEL_NOT_FOUND'
                        },
                            null
                        );
                        break;

                    case 'CALLCENTER_NOT_FOUND':
                        callback({
                            code: status.INTERNAL,
                            name: 'CALLCENTER_NOT_FOUND',
                            message: 'CALLCENTER_NOT_FOUND'
                        },
                            null
                        )
                        break;

                    default:
                        console.error(e);

                        callback({
                            code: status.INTERNAL,
                            name: 'UNKNOWN_ERROR',
                            message: 'Unknown error occured, please try again later'
                        },
                            null
                        );
                }
            }
        }

    addAnnounceBot: handleUnaryCall<RegisterCallcenterRequest, Empty> =
        async (req: ServerUnaryCall<RegisterCallcenterRequest>,
            callback: sendUnaryData<Empty>) => {
            const channelId = req.request.getChannelid();

            try {
                await prisma.$transaction(async prisma => {
                    await prisma.adminChannel
                        .update({
                            where: {
                                channelId: channelId
                            },
                            data: {
                                announceBot: {
                                    create: {

                                    }
                                }
                            }
                        }).catch((e: any) => {
                            console.error(e);
                            throw new Error('ALREADY_SET_OR_CHANNEL_NOT_FOUND');
                        });
                }, {
                    isolationLevel: 'RepeatableRead'
                });

                callback(null, new Empty());
            } catch (e: any) {
                callback({
                    name: e.message,
                    message: e.message,
                    code: status.INTERNAL
                },
                    null
                );
            }
        }

    removeAnnounceBot: handleUnaryCall<ChannelId, Empty> =
        async (req: ServerUnaryCall<ChannelId>,
            callback: sendUnaryData<Empty>) => {
            const channelId = req.request.getChannelid();

            try {
                await prisma.$transaction(async prisma => {
                    await prisma.adminChannel
                        .update({
                            where: {
                                channelId: channelId
                            },
                            data: {
                                announceBot: {
                                    delete: true
                                }
                            }
                        }).catch((e: any) => {
                            console.error(e);
                            throw new Error('CHANNEL_OR_BOT_NOT_FOUND');
                        });
                }, {
                    isolationLevel: 'RepeatableRead'
                });

                callback(null, new Empty());
            } catch (e: any) {
                callback({
                    name: e.message,
                    message: e.message,
                    code: status.INTERNAL
                },
                    null
                );
            }
        }

    getAnounceBotByChannelId: handleUnaryCall<ChannelId, AnnouneBotExists> =
        async (req: ServerUnaryCall<ChannelId>, callback: sendUnaryData<AnnouneBotExists>) => {
            const channelId = req.request.getChannelid();

            try {
                const exists = await prisma.$transaction(async prisma => {
                    const channel = await prisma
                        .adminChannel.findUnique({
                            include: {
                                announceBot: true
                            },
                            where: {
                                channelId: channelId
                            }
                        });

                    if (!channel) {
                        throw new Error('CHANNEL_NOT_FOUND');
                    }

                    return !!channel.announceBot;
                }, {
                    isolationLevel: 'ReadCommitted'
                });

                const response = new AnnouneBotExists();
                response.setExists(exists);
                callback(null, response);
            } catch (e: any) {
                callback({
                    name: e.message,
                    message: e.message,
                    code: status.INTERNAL
                },
                    null
                );
            }
        }

    getWorkday: handleUnaryCall<GetStatusRequest, WorkdayData> =
        getWorkday;


    setWorkday: handleUnaryCall<WorkdayData, WorkdayData> =
        setWorkday;
}
