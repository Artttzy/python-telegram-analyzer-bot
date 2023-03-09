import { handleUnaryCall, sendUnaryData, ServerUnaryCall, status } from "grpc";
import { ISubscribtionServiceServer } from "../grpc/sub-unsub_grpc_pb";
import {
    Admin,
    AdminChannel,
    AdminChannelId,
    AdminChannelList,
    AdminList,
    AdminStat,
    AgeRequest,
    AnnounceMessagesResponse,
    AnswerTime,
    CAStat,
    CAStats,
    ChannelMessage,
    ChannelMessageList,
    ConnectedChannelsCountResponse,
    DayAnswerStat,
    DayAnswerStats,
    EmptyMessage,
    EventResponse,
    GenderRequest,
    JoinLeftInfo,
    JoinLeftRequest,
    JoinLeftStatisticsResponse,
    NullableAdmin,
    PushSubscriberHistoryMessage,
    SaveMessageRequest,
    SetAnnounceMessagesRequest,
    SubscriberHistory,
    SubscriberHistoryElement,
    SubscriberPeak,
    SubUnsubEvent,
    TicketStatsRequest,
    UserIdRequest,
    UserList
} from "../grpc/sub-unsub_pb";
import { getTodayServerSubStats, insertServerStatEntry, updateServerStatEntry } from "../util/prisma-tools";
import { Timestamp } from "google-protobuf/google/protobuf/timestamp_pb";
import { prisma } from '../util/prisma-factory'
import { Decimal } from "@prisma/client/runtime";
import { getJoinLeftMessage, setJoinLeftMessage } from "../util/announce_message_config";

const UTC_TZ = 6; // Kazakhstan

export class SubUnsubServer implements ISubscribtionServiceServer {
    getTodayPeak = async (channelId: ServerUnaryCall<AdminChannelId>, callback: sendUnaryData<SubscriberPeak>) => {
        const channel = channelId.request.getChannelid();

        const todayPeak = await prisma.subscriberHistory
            .findFirst({
                include: {
                    channel: true
                },
                where: {
                    channel: {
                        channelId: channel
                    }
                },
                orderBy: {
                    measureTime: 'desc'
                }
            }).catch((e: Error) => console.error(e));

        if (!todayPeak) {
            callback({
                code: status.INTERNAL,
                message: 'An exception occured',
                name: 'INTERNAL_EXCEPTION'
            }, null)
            return;
        }

        const peak = new SubscriberPeak();
        peak.setValue(todayPeak.subscriberCount);
        peak.setDate(Timestamp.fromDate(todayPeak.measureTime));
        callback(null, peak);
    }
    triggerEvent: handleUnaryCall<SubUnsubEvent, EventResponse> =
        (subUnsubEvent: ServerUnaryCall<SubUnsubEvent>, callback: sendUnaryData<EventResponse>) => {

            const cid = subUnsubEvent.request.getChannelid();
            const id = subUnsubEvent.request.getId();
            const substatus = subUnsubEvent.request.getSubstatus();
            const datetime = subUnsubEvent.request.getTime()!.toDate();

            prisma.event.create({
                data: {
                    userId: id,
                    channelId: cid,
                    eventStatus: substatus,
                    eventTime: datetime
                }
            }).catch((e: Error) => console.error(e));

            callback(null, new EventResponse())
        }

    joinLeftStatistics: handleUnaryCall<JoinLeftRequest, JoinLeftStatisticsResponse> =
        async (req: ServerUnaryCall<JoinLeftRequest>, callback: sendUnaryData<JoinLeftStatisticsResponse>) => {
            const day = new Date(req.request.getDay()!.toDate());
            const channelId = req.request.getChannelid();

            const start = new Date(day);
            start.setUTCHours(0, 0, 0, 0);
            start.setUTCHours(start.getUTCHours() - UTC_TZ);
            const end = new Date(start);
            end.setUTCHours(end.getUTCHours() + 24);

            const joined = await prisma.event
                .findMany({
                    where: {
                        eventTime: {
                            gte: start,
                            lte: end
                        },
                        eventStatus: 'join',
                        channelId: channelId
                    },
                    distinct: 'userId'
                });

            const left = await prisma.event
                .findMany({
                    where: {
                        eventTime: {
                            gte: start,
                            lte: end
                        },
                        eventStatus: 'left',
                        channelId: channelId
                    },
                    distinct: 'userId'
                });

            const response = new JoinLeftStatisticsResponse();

            for (let d = new Date(start); d.getTime() < end.getTime(); d.setUTCHours(d.getUTCHours() + 1)) {
                let dEnd = new Date(d);
                dEnd.setUTCHours(dEnd.getUTCHours() + 1);

                const filterJoin = joined.filter(j => j.eventTime >= d && j.eventTime < dEnd);
                const filterLeft = left.filter(l => l.eventTime >= d && l.eventTime < dEnd);

                const lTime = new Date(d);
                lTime.setUTCHours(lTime.getUTCHours() + UTC_TZ);
                const hh = lTime.getUTCHours()
                    .toString().padStart(2, '0');
                const mm = lTime.getUTCMinutes()
                    .toString().padStart(2, '0');

                const joinInfo = new JoinLeftInfo();
                joinInfo.setTime(`${hh}:${mm}`);
                joinInfo.setValue(filterJoin.length);

                const leftInfo = new JoinLeftInfo();
                leftInfo.setTime(`${hh}:${mm}`);
                leftInfo.setValue(filterLeft.length);

                response.addJoined(joinInfo);
                response.addLeft(leftInfo);
            }

            callback(null, response);
        }

    connectedChannelsCount: handleUnaryCall<EmptyMessage, ConnectedChannelsCountResponse> =
        async (req: ServerUnaryCall<EmptyMessage>, callback: sendUnaryData<ConnectedChannelsCountResponse>) => {
            const channels = await prisma.adminChannel.count({
                distinct: ['channelId']
            });

            const response = new ConnectedChannelsCountResponse();
            response.setChannelcount(channels);
            callback(null, response);
        }

    setAdminChannel: handleUnaryCall<AdminChannel, EmptyMessage> =
        async (req: ServerUnaryCall<AdminChannel>, callback: sendUnaryData<EmptyMessage>) => {
            const cid = req.request.getChannelid();
            const channelName = req.request.getChannelname();

            prisma.adminChannel.create({
                data: {
                    channelId: cid,
                    channelName: channelName
                }
            }).catch((e: Error) => console.error(e));

            callback(null, new EmptyMessage());
        }

    getAdminChannels: handleUnaryCall<EmptyMessage, AdminChannelList> =
        async (req: ServerUnaryCall<EmptyMessage>, callback: sendUnaryData<AdminChannelList>) => {
            const channels = await prisma.adminChannel.findMany();
            const response = new AdminChannelList();

            channels.forEach((ch, i) => {
                const channel = new AdminChannel();
                channel
                    .setChannelid(ch.channelId)
                    .setChannelname(ch.channelName);

                response.addChannels(channel, i);
            });

            callback(null, response);
        }

    addAdmin: handleUnaryCall<Admin, EmptyMessage> =
        async (req: ServerUnaryCall<Admin>, callback: sendUnaryData<EmptyMessage>) => {
            const id = req.request.getUserid();
            const username = req.request.getUsername();
            const superuser = false;

            prisma.admin
                .create({
                    data: {
                        userId: id,
                        username,
                        superuser
                    }
                }).catch((e: Error) => console.error(e));

            callback(null, new EmptyMessage());
        }

    getAdmins: handleUnaryCall<EmptyMessage, AdminList> =
        async (req: ServerUnaryCall<EmptyMessage>, callback: sendUnaryData<AdminList>) => {
            const admins = await prisma.admin.findMany();
            const list = new AdminList();

            admins.forEach((adm, i) => {
                const admin = new Admin();
                admin
                    .setUserid(adm.userId)
                    .setSuperuser(adm.superuser)
                    .setUsername(adm.username);

                list.addAdmins(admin, i);
            })

            callback(null, list);
        }

    removeAdmin: handleUnaryCall<Admin, EmptyMessage> =
        async (req: ServerUnaryCall<Admin>, callback: sendUnaryData<EmptyMessage>) => {
            const id = req.request.getUserid();
            const admin = await prisma.admin.findFirst({
                where: {
                    userId: id
                }
            });

            if (!admin) {
                callback({
                    message: 'Admin not found',
                    code: 3,
                    name: 'NOT_FOUND'
                }, null);

                return;
            }

            if (admin.superuser) {
                callback({
                    message: 'Admin cant be deleted',
                    code: 3,
                    name: 'ADMIN_IS_SUPERUSER'
                }, null);

                return;
            }

            prisma.admin.delete({
                where: {
                    id: admin.id
                }
            }).catch((e: Error) => console.error(e));

            callback(null, new EmptyMessage());
        }

    getAdminByUserId: handleUnaryCall<UserIdRequest, NullableAdmin> =
        async (req: ServerUnaryCall<UserIdRequest>, callback: sendUnaryData<NullableAdmin>) => {
            const id = req.request.getUserid();
            const admin = await prisma.admin.findFirst({
                where: {
                    userId: id
                }
            });

            const data = new NullableAdmin();

            if (admin) {
                const adminBody = new Admin();
                adminBody
                    .setUserid(admin.userId)
                    .setSuperuser(admin.superuser)
                    .setUsername(admin.username);

                data.setAdmin(adminBody);
            } else {
                data.setEmpty(new EmptyMessage());
            }

            callback(null, data);
        }

    getSubscriberHistory: handleUnaryCall<AdminChannelId, SubscriberHistory> =
        async (req: ServerUnaryCall<AdminChannelId>, callback: sendUnaryData<SubscriberHistory>) => {
            const now = new Date();
            // now.setUTCHours(now.getUTCHours() - UTC_TZ);
            const twoWeeksAgo = new Date(now);
            twoWeeksAgo.setUTCHours(twoWeeksAgo.getUTCHours() - 14 * 24);
            const cid = req.request.getChannelid();

            const channels = await prisma.subscriberHistory
                .findMany({
                    include: {
                        channel: true
                    },
                    where: {
                        AND: [{
                            measureTime: {
                                gte: twoWeeksAgo,
                                lte: now
                            }
                        },
                        {
                            channel: {
                                channelId: cid
                            }
                        }]
                    },
                    orderBy: {
                        measureTime: 'desc'
                    }
                }).catch((e: Error) => console.error(e));

            if (!channels) {
                callback({
                    code: status.INTERNAL,
                    message: 'An exception occured',
                    name: 'INTERNAL_EXCEPTION'
                }, null)
                return;
            }

            const history = new SubscriberHistory();

            channels.forEach((el, i) => {
                const elem = new SubscriberHistoryElement();
                elem.setValue(el.subscriberCount);
                const lDate = new Date(el.measureTime);
                lDate.setUTCHours(lDate.getUTCHours() + UTC_TZ);
                const hh = lDate.getUTCHours()
                    .toString().padStart(2, '0');
                const mm = lDate.getUTCMinutes()
                    .toString().padStart(2, '0');

                // elem.setDate(`${hh}:${mm}`);
                console.log(lDate.toISOString());
                elem.setDate(lDate.toISOString().split('T')[0]);
                history.addHistory(elem, i);
            });

            callback(null, history);
        }

    pushSubscriberHistory: handleUnaryCall<PushSubscriberHistoryMessage, EmptyMessage> =
        async (req: ServerUnaryCall<PushSubscriberHistoryMessage>, callback: sendUnaryData<EmptyMessage>) => {
            const cid = req.request.getChannelid();
            const subscriberCount = req.request.getValue();
            const time = new Date();
            const todayStats = await getTodayServerSubStats(prisma, cid)
                .catch((e: Error) => {
                    console.log(e)
                    return undefined;
                });

            if (!todayStats) {
                callback({
                    code: status.INTERNAL,
                    message: 'An exception occured',
                    name: 'INTERNAL_EXCEPTION'
                }, null)
                return;
            }

            if (todayStats.length !== 0) {
                const historyItem = todayStats[todayStats.length - 1];

                if (historyItem.subscriberCount < subscriberCount) {
                    historyItem.measureTime = time;
                    historyItem.subscriberCount = subscriberCount;
                    const result = await updateServerStatEntry(prisma, historyItem)
                        .catch((e: Error) => {
                            console.log(e)
                            return undefined;
                        });

                    if (!result) {
                        callback({
                            code: status.INTERNAL,
                            message: 'An exception occured',
                            name: 'INTERNAL_EXCEPTION'
                        }, null)
                        return;
                    }
                }
            } else {
                const result = await insertServerStatEntry(prisma, cid, time, subscriberCount)
                    .catch((e: Error) => {
                        console.log(e)
                        return undefined;
                    });

                if (!result) {
                    callback({
                        code: status.INTERNAL,
                        message: 'An exception occured',
                        name: 'INTERNAL_EXCEPTION'
                    }, null)
                    return;
                }
            }

            callback(null, new EmptyMessage());
        }

    saveMessage: handleUnaryCall<SaveMessageRequest, EmptyMessage> =
        async (req: ServerUnaryCall<SaveMessageRequest>, callback: sendUnaryData<EmptyMessage>) => {
            const mid = req.request.getMessageid();
            const cid = req.request.getChannelid();
            const time = new Date();

            const channel = await prisma.adminChannel
                .findUnique({
                    where: {
                        channelId: cid
                    }
                });

            if (!channel) {
                callback({
                    code: status.NOT_FOUND,
                    message: 'Channel not found',
                    name: 'ECHANNEL_NOT_FOUND'
                }, null);

                return
            }

            prisma.message
                .create({
                    data: {
                        channelKey: channel.id,
                        measureTime: time,
                        messageId: mid
                    }
                }).catch((e: Error) => {
                    console.error(e);
                });

            callback(null, new EmptyMessage());
        }

    getMessages: handleUnaryCall<AdminChannelId, ChannelMessageList> =
        async (req: ServerUnaryCall<AdminChannelId>, callback: sendUnaryData<ChannelMessageList>) => {
            const cid = req.request.getChannelid();
            const now = new Date();
            now.setUTCHours(23, 59, 59, 999);
            now.setUTCHours(now.getUTCHours() - (UTC_TZ - now.getTimezoneOffset()));


            const twoWeeksAgo = new Date(now);
            twoWeeksAgo.setUTCHours(twoWeeksAgo.getUTCHours() - 24 * 14);

            const messages = await prisma
                .message.findMany({
                    include: {
                        channel: true
                    },
                    where: {
                        channel: {
                            channelId: cid
                        },
                        measureTime: {
                            lte: now,
                            gte: twoWeeksAgo
                        }
                    }
                })
                .catch((e: Error) => {
                    console.error(e);
                    return undefined;
                });

            if (!messages) {
                callback({
                    code: status.INTERNAL,
                    message: 'An exception occured',
                    name: 'INTERNAL_EXCEPTION'
                }, null)
                return;
            }

            const response = new ChannelMessageList();
            response.setChannelid(cid);

            messages.forEach((msg, i) => {
                const msgDate = new Timestamp();
                msgDate.fromDate(msg.measureTime);

                const message = new ChannelMessage();
                message.setMessageid(msg.messageId);
                message.setMessagedate(msgDate);

                response.addMessages(message, i);
            });

            callback(null, response);
        }

    deleteAdminChannel: handleUnaryCall<AdminChannelId, EmptyMessage> =
        async (req: ServerUnaryCall<AdminChannelId>, callback: sendUnaryData<EmptyMessage>) => {
            const cid = req.request.getChannelid();

            prisma.adminChannel
                .delete({
                    where: {
                        channelId: cid
                    }
                })
                .catch((e: Error) => {
                    console.error(e);
                });

            callback(null, new EmptyMessage());
        }

    writeGenderStats: handleUnaryCall<GenderRequest, EmptyMessage> =
        async (req: ServerUnaryCall<GenderRequest>, callback: sendUnaryData<EmptyMessage>) => {
            const userId = req.request.getUserid();
            const gender = req.request.getGender();
            const cid = req.request.getChannelid();

            const userinfo = await prisma.cAStats
                .findUnique({
                    where: {
                        userId_channelId: {
                            userId: userId,
                            channelId: cid
                        }
                    }
                });

            if (!userinfo) {
                await prisma.cAStats.create({
                    data: {
                        channelId: cid,
                        userId: userId,
                        gender: gender
                    }
                });
            } else if (!userinfo.gender) {
                await prisma.cAStats.update({
                    where: {
                        id: userinfo.id
                    },
                    data: {
                        gender: gender
                    }
                });
            }

            callback(null, new EmptyMessage());
        }

    writeAgeStats: handleUnaryCall<AgeRequest, EmptyMessage> =
        async (req: ServerUnaryCall<AgeRequest>, callback: sendUnaryData<EmptyMessage>) => {
            const userId = req.request.getUserid();
            const age = req.request.getAge();
            const decimalAge = new Decimal(age);
            const cid = req.request.getChannelid();

            const userinfo = await prisma.cAStats
                .findUnique({
                    where: {
                        userId_channelId: {
                            userId: userId,
                            channelId: cid
                        }
                    }
                });

            if (!userinfo) {
                await prisma.cAStats.create({
                    data: {
                        channelId: cid,
                        userId: userId,
                        age: decimalAge
                    }
                });
            } else if (!userinfo.age) {
                await prisma.cAStats.update({
                    where: {
                        id: userinfo.id
                    },
                    data: {
                        age: decimalAge
                    }
                });
            }

            callback(null, new EmptyMessage());
        }

    getStatsPerChannel: handleUnaryCall<AdminChannelId, CAStats> =
        async (req: ServerUnaryCall<AdminChannelId>, callback: sendUnaryData<CAStats>) => {
            const cid = req.request.getChannelid();

            const stats = await prisma.cAStats
                .findMany({
                    where: {
                        channelId: cid
                    }
                });

            const response = new CAStats();
            response.setChannelid(cid);

            stats.forEach((st, i) => {
                const stat = new CAStat();
                stat.setUserid(st.userId);
                stat.setGender(st.gender ?? '');
                stat.setAge(Number.parseInt(st.age?.toString() ?? '0'));
                response.addStats(stat, i);
            });

            callback(null, response);
        }

    getChannelJoinList: handleUnaryCall<AdminChannelId, UserList> =
        async (req: ServerUnaryCall<AdminChannelId>, callback: sendUnaryData<UserList>) => {
            const cid = req.request.getChannelid();

            const joined = await prisma.event
                .findMany({
                    select: {
                        userId: true
                    },
                    distinct: ['userId'],
                    where: {
                        channelId: cid
                    }
                })

            const stats = new UserList();

            joined.forEach((u, i) => {
                const user = new UserIdRequest();
                user.setUserid(u.userId);
                stats.addUsers(user, i);
            });

            callback(null, stats);
        }

    getAverageAnswerTime: handleUnaryCall<TicketStatsRequest, AnswerTime> =
        async (req: ServerUnaryCall<TicketStatsRequest>,
            callback: sendUnaryData<AnswerTime>) => {
            const channelId = req.request.getChannelid();
            const day = req.request.getDay()!.toDate();
            const start = new Date(day);
            start.setUTCHours(0, 0, 0, 0);
            start.setUTCHours(start.getUTCHours() - UTC_TZ);
            const end = new Date(day);
            end.setUTCHours(23, 59, 59, 999);
            end.setUTCHours(end.getUTCHours() - UTC_TZ);

            try {
                const response = await prisma
                    .$transaction(async prisma => {
                        const channel = await prisma
                            .adminChannel.findUnique({
                                include: {
                                    callCenters: {
                                        include: {
                                            tickets: {
                                                where: {
                                                    openTime: {
                                                        gte: start,
                                                        lte: end,
                                                    }
                                                }
                                            }
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
                            throw new Error('CALLCENTER_NOT_CREATED');
                        }

                        const tickets = channel.callCenters.tickets;
                        const avgMillis = tickets.length === 0 ? 0
                            : tickets.reduce((sum, current) => {
                                if (!current.findTime || !current.answerTime) {
                                    return sum;
                                }

                                const diff = current.answerTime.getTime() - current.findTime.getTime();
                                return sum + diff;
                            }, 0) / tickets.length;

                        const response = new AnswerTime();
                        const time = Timestamp.fromDate(new Date(avgMillis));
                        // console.log(avgMillis);
                        response.setAnswertime(time);
                        response.setTicketcount(tickets.length);
                        return response;
                    }, {
                        isolationLevel: 'ReadCommitted'
                    });

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

    getAnswerTimeForEach: handleUnaryCall<TicketStatsRequest, DayAnswerStats> =
        async (req: ServerUnaryCall<TicketStatsRequest>, callback: sendUnaryData<DayAnswerStats>) => {
            const channelId = req.request.getChannelid();
            const day = req.request.getDay()!.toDate();
            const start = new Date(day);
            start.setUTCHours(0 - UTC_TZ, 0, 0, 0);
            start.setUTCHours(start.getUTCHours() - 13 * 24);

            const end = new Date(start);
            end.setUTCHours(end.getUTCHours() + 14 * 24);

            try {
                const response = await prisma
                    .$transaction(async prisma => {
                        const channel = await prisma
                            .adminChannel.findUnique({
                                include: {
                                    callCenters: {
                                        include: {
                                            agents: {
                                                include: {
                                                    tickets: {
                                                        where: {
                                                            openTime: {
                                                                gte: start,
                                                                lte: end
                                                            }
                                                        }
                                                    }
                                                }
                                            }
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
                            throw new Error('CALLCENTER_NOT_CREATED');
                        }

                        const response = new DayAnswerStats();

                        let i = 0;
                        for (let d = new Date(start); d <= end; d.setUTCHours(d.getUTCHours() + 24), ++i) {
                            const dEnd = new Date(d);
                            dEnd.setUTCHours(dEnd.getUTCHours() + 24);
                            const stat = new DayAnswerStat();
                            stat.setDay(Timestamp.fromDate(d));

                            const adminStats = channel.callCenters.agents
                                .map(agent => {
                                    const admin = new AdminStat();
                                    admin.setUserid(agent.userId);
                                    const dayTickets = agent.tickets
                                        .filter(ticket =>
                                            ticket.openTime >= d && ticket.openTime < dEnd);

                                    const avgMillis = dayTickets.length === 0 ? 0
                                        : dayTickets.reduce((sum, current) => {
                                            if (!current.findTime || !current.answerTime) {
                                                return sum;
                                            }

                                            const diff = current.answerTime.getTime() - current.findTime.getTime();
                                            return sum + diff;
                                        }, 0) / dayTickets.length;

                                    admin.setTicketcount(dayTickets.length);
                                    admin.setAnswertime(Timestamp.fromDate(new Date(avgMillis)));
                                    return admin;
                                });

                            stat.setStatsList(adminStats);
                            response.addStats(stat, i);
                        }

                        return response;
                    }, {
                        isolationLevel: 'ReadCommitted'
                    });

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


    setJoinMessageId: handleUnaryCall<SetAnnounceMessagesRequest, EmptyMessage> =
        (req, callback) => setJoinLeftMessage(req, callback, 'JOIN');

    setLeftMessageId: handleUnaryCall<SetAnnounceMessagesRequest, EmptyMessage> =
        (req, callback) => setJoinLeftMessage(req, callback, 'LEFT');

    getJoinMessage: handleUnaryCall<AdminChannelId, AnnounceMessagesResponse> =
        (req, callback) => getJoinLeftMessage(req, callback, 'JOIN');

    getLeftMessage: handleUnaryCall<AdminChannelId, AnnounceMessagesResponse> =
        (req, callback) => getJoinLeftMessage(req, callback, 'LEFT');
}
