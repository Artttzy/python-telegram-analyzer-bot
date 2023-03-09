import { handleUnaryCall, sendUnaryData, ServerUnaryCall, status } from "grpc";
import { GetStatusRequest, WorkdayData } from "../grpc/ticket-bot_pb";
import { prisma } from './prisma-factory'

export const getWorkday: handleUnaryCall<GetStatusRequest, WorkdayData> =
    async (req: ServerUnaryCall<GetStatusRequest>, callback: sendUnaryData<WorkdayData>) => {
        const agentId = req.request.getUserid();
        const callcenterId = req.request.getCallcenterid();

        try {
            const data = await prisma.$transaction(async prisma => {
                const data = await prisma.callCenter
                    .findUnique({
                        include: {
                            agents: {
                                where: {
                                    userId: agentId
                                },
                                include: {
                                    callCenter: true
                                }
                            }
                        },
                        where: {
                            externalId: callcenterId
                        }
                    });

                if (!data || data.agents.length === 0) {
                    throw new Error('AGENT_NOT_FOUND');
                }

                return data.agents[0];
            }, {
                isolationLevel: 'ReadCommitted'
            });

            const response = new WorkdayData();
            response.setAgentid(data.userId);
            response.setCallcenterid(data.callCenter.externalId);
            response.setIsworking(data.isWorking);
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


export const setWorkday: handleUnaryCall<WorkdayData, WorkdayData> =
    async (req: ServerUnaryCall<WorkdayData>, callback: sendUnaryData<WorkdayData>) => {
        const agentId = req.request.getAgentid();
        const callcenterId = req.request.getCallcenterid();
        const isWorking = req.request.getIsworking();

        try {
            const data = await prisma.$transaction(async prisma => {
                const callcenter = await prisma.callCenter
                    .findUnique({
                        include: {
                            agents: {
                                where: {
                                    userId: agentId
                                }
                            }
                        },
                        where: {
                            externalId: callcenterId
                        }
                    });

                if (!callcenter || callcenter.agents.length === 0) {
                    throw new Error('AGENT_NOT_FOUND');
                }

                const updated = await prisma.supportAgent
                    .update({
                        include: {
                            callCenter: true
                        },
                        where: {
                            userId_callCenterKey: {
                                userId: agentId,
                                callCenterKey: callcenter.id
                            }
                        },
                        data: {
                            isWorking: isWorking
                        }
                    });

                return updated;
            }, {
                isolationLevel: 'RepeatableRead'
            });

            const response = new WorkdayData();
            response.setAgentid(data.userId);
            response.setCallcenterid(data.callCenter.externalId);
            response.setIsworking(data.isWorking);
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