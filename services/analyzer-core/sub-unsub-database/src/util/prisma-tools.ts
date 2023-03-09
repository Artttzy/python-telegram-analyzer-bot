import { PrismaClient } from "@prisma/client";

// const UTC_TZ = 6; // Kazakhstan

export async function getTodayServerSubStats(prisma: PrismaClient, channelId: string) {
    const dayStart = new Date();
    dayStart.setUTCHours(0, 0, 0, 0);
    // dayStart.setUTCHours(dayStart.getUTCHours() - UTC_TZ);
    const dayEnd = new Date();
    dayEnd.setUTCHours(23, 59, 59, 999);
    // dayEnd.setUTCHours(dayEnd.getUTCHours() - UTC_TZ);

    const stats = await prisma.subscriberHistory
        .findMany({
            include: {
                channel: true
            },
            where: {
                AND: [{
                    channel: {
                        channelId: channelId
                    }
                },
                {
                    measureTime: {
                        gte: dayStart,
                        lte: dayEnd
                    }
                }]
            }
        });

    return stats;
}

export async function updateServerStatEntry(prisma: PrismaClient, historyItem: any) {
    return await prisma.subscriberHistory.update({
        data: {
            id: historyItem.id,
            measureTime: historyItem.measureTime,
            subscriberCount: historyItem.subscriberCount
        },
        where: {
            id: historyItem.id
        }
    });
}

export async function insertServerStatEntry(prisma: PrismaClient, channelId: string, time: Date, subscriberCount: number) {
    const channel = await prisma.adminChannel
        .findUniqueOrThrow({
            where: {
                channelId: channelId
            }
        });

    return await prisma.subscriberHistory
        .create({
            data: {
                channelKey: channel.id,
                measureTime: time,
                subscriberCount: subscriberCount
            }
        });
}