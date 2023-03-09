import { Request, Response } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export const logTelegramRedirect = async (req: Request, response: Response) => {
    const from = req.query['from']?.toString() ?? '';
    const to = req.query['to']?.toString() ?? '';
    const user = req.cookies['user'];

    if (!user) {
        const id = uuidv4();
        response.cookie('user', id);

        try {
            const channel = await prisma.adminChannel
                .findUnique({
                    where: {
                        channelId: from,
                    }
                });

            if (channel) {
                const time = new Date();

                await prisma.supportRedirect.create({
                    data: {
                        clickTime: time,
                        count: 1,
                        channelKey: channel.id
                    }
                });
            }
        } catch (e: any) {
            console.error(e);
        }
    }

    response.redirect(to);
}