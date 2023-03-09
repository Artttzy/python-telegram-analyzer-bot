import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters.text import Text
from aiogram.types import ReplyKeyboardRemove
import ticket_bot_pb2
import factory
import grpc_calls
import grpc
from background_tasks import check_available
from settings import BOT_TOKEN


logging.basicConfig(level=logging.INFO)
dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)


class MenuState(StatesGroup):
    menu = State()
    ticket_open_client = State()
    ticket_open_agent = State()


@dp.message(commands=["start"])
async def cmd_start(message: types.Message, state: FSMContext):
    status: ticket_bot_pb2.SupportStatus = grpc_calls.get_status(
        user_id=message.from_user.id)

    if status.userState == ticket_bot_pb2.USER:
        if status.supportState == ticket_bot_pb2.IDLE:
            await state.set_state(MenuState.menu)
            keyboard = factory.create_menu_keyboard()
            await message.answer(
                'Здравствуйте! Чтобы обратиться в поддержку ' +
                'нажмите кнопку снизу',
                reply_markup=keyboard
            )
        elif status.supportState == ticket_bot_pb2.TICKET_PENDING_ANSWER:
            await state.set_state(MenuState.ticket_open_client)
            ticketId = status.ticketData.ticketId
            await message.answer(
                f'Вас связали с блогером.'
            )
        elif status.supportState == ticket_bot_pb2.TICKET_OPEN:
            await state.set_state(MenuState.ticket_open_client)
            ticketId = status.ticketData.ticketId
            await message.answer(
                f'Вас связали с блогером.'
            )
        else:
            raise ValueError()

    elif status.userState == ticket_bot_pb2.AGENT:
        if status.HasField('ticketData'):
            await state.set_state(MenuState.ticket_open_agent)
            ticketId = status.ticketData.ticketId
            await message.answer(
                f'Здравствуйте, агент поддержки, ' +
                f'сейчас у Вас открыт тикет №{status.ticketData.ticketId}',
                reply_markup=factory.create_close_ticket_button(ticketId)
            )
        else:
            await message.answer(
                f'Здравствуйте, агент поддержки, у Вас сейчас нет открытых тикетов'
            )


@dp.message(MenuState.ticket_open_client)
async def on_client_msg(message: types.Message, state: FSMContext):
    if (message.text.startswith("Открыть тикет")):
        return
    status: ticket_bot_pb2.SupportStatus = grpc_calls.get_status(
        user_id=message.from_user.id)

    if status.HasField('ticketData'):
        should_log = grpc_calls.log_user_message(
            ticket_id=status.ticketData.ticketId,
            message_id=message.message_id
        ).value

        if status.ticketData.HasField('agentId'):
            agentId = status.ticketData.agentId
            await message.send_copy(int(agentId))

            if should_log:
                await message.reply('_info: сообщение доставлено_', parse_mode='Markdown')
    pass


@dp.message(MenuState.ticket_open_agent)
async def on_agent_msg(message: types.Message, state: FSMContext):
    status: ticket_bot_pb2.SupportStatus = grpc_calls.get_status(
        user_id=message.from_user.id)

    if status.HasField('ticketData'):
        clientId = status.ticketData.userId
        await message.send_copy(int(clientId))

        await message.reply('_info: сообщение доставлено_', parse_mode='Markdown')
        grpc_calls.log_agent_message(status.ticketData.ticketId)


@dp.message(Text(text='Открыть тикет 🎫'), MenuState.menu)
@dp.callback_query(Text(text_startswith='open_ticket'))
async def open_ticket(message: types.Message, state: FSMContext):
    try:
        open_ticket_response = grpc_calls.open_ticket(message.from_user.id)
        await state.set_state(MenuState.ticket_open_client)

        if open_ticket_response.HasField('agentId'):
            await message.answer(
                f'Вас связали с блогером.'
            )

            await bot.send_message(
                chat_id=int(open_ticket_response.agentId),
                text=f'Вы назачены агентом поддержки на тикет №{open_ticket_response.ticketId}',
                reply_markup=factory.create_close_ticket_button(
                    open_ticket_response.ticketId)
            )

        else:
            await message.answer(
                f'Вас связали с блогером.'
            )

    except grpc.RpcError as e:
        err_code = e.args[0].details
        if err_code == 'CALLCENTER_NOT_FOUND':
            await message.answer(
                'Бот для поддержки был неправильно настроен (центр поддержки не найден)'
            )
        elif err_code == 'BAD_CHANNEL_ID':
            await message.answer(
                'Бот для поддержки был неправильно настроен (центр поддержки не соответствует назначенному каналу)'
            )
        elif err_code == 'TICKET_ALREADY_OPENED':
            await message.answer(
                'Вы уже открыли тикет для поддержки. Дождитесь ответа или закройте существующий тикет'
            )
        else:
            await message.answer(
                'Произошла ошибка при обращении. Пожалуйста, попробуйте позднее'
            )


@dp.callback_query(Text(text_startswith='close_ticket'))
async def close_ticket(callback: types.CallbackQuery, state: FSMContext):
    ticketId = callback.data.split('_')[-1]
    userId = callback.from_user.id
    try:
        closed_ticket: ticket_bot_pb2.TicketData = grpc_calls.close_ticket(
            ticketId)

        await bot.send_message(
            chat_id=userId,
            text='Тикет успешно закрыт')

        await state.set_state(MenuState.menu)
        await callback.message.delete()

        if closed_ticket.userId == str(userId):
            if closed_ticket.HasField('agentId'):
                await bot.send_message(
                    chat_id=int(closed_ticket.agentId),
                    text=f'Тикет №{closed_ticket.ticketId} закрыт клиентом')
        else:
            await bot.send_message(
                chat_id=int(closed_ticket.userId),
                text=f'Сессия закончена, если у вас возникли дополнительные вопросы, откройте тикет еще раз.',
                reply_markup=factory.create_open_ticket_button()
            )

    except grpc.RpcError as e:
        await bot.send_message(
            chat_id=callback.from_user.id,
            text='Произошла ошибка при закрытии тикета.' +
            'Используйте /start для перезагрузки бота'
        )
        pass


async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(check_available.main(bot=bot))
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
