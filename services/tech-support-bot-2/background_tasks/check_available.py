from aiogram import Bot
import factory
import asyncio
from settings import CALL_CENTER_ID
import grpc_calls
import ticket_bot_pb2


async def handle_update(bot,
                        ticket: ticket_bot_pb2.TicketData):
    if ticket.HasField('agentId'):
        # clientId = ticket.userId
        agentId = ticket.agentId
        ticketId = ticket.ticketId
        username = ticket.username

        await bot.send_message(
            chat_id=int(agentId),
            text=f'Вы назачены агентом поддержки на тикет №{ticketId}',
            reply_markup=factory.create_goto_user_keyboard_username(ticket_id=ticketId,
                                                                    username=username)
        )


async def check_available(bot: Bot):
    while True:
        ticket_update: ticket_bot_pb2.TicketUpdateResponse \
            = grpc_calls.check_available_agent(CALL_CENTER_ID)
        if ticket_update.HasField('ticket'):
            await handle_update(bot=bot, ticket=ticket_update.ticket)
        else:
            break


async def main(bot):
    while True:
        try:
            await check_available(bot=bot)
        except Exception:
            pass

        await asyncio.sleep(10)
