import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters.text import Text
from aiogram.types import InlineKeyboardMarkup
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

    if status.userState == ticket_bot_pb2.AGENT:
        await message.answer(f'Здравствуйте, агент поддержки',
                             reply_markup=factory.create_workday_keyboard())


@dp.message(Text(text_startswith='Рабочий день'))
async def cmd_workday(message: types.Message, state: FSMContext):
    status: ticket_bot_pb2.SupportStatus = grpc_calls.get_status(
        user_id=message.from_user.id)

    if status.userState == ticket_bot_pb2.AGENT:
        workday: ticket_bot_pb2.WorkdayData = grpc_calls.get_workday_status(
            user_id=message.from_user.id)

        if workday.isWorking:
            await message.answer('У вас сейчас рабочее время',
                                 reply_markup=factory.set_workday_keyboard(
                                     text='Закончить рабочий день',
                                     set_enabled=False)
                                 )
        else:
            await message.answer('У вас сейчас отдых',
                                 reply_markup=factory.set_workday_keyboard(
                                     text='Начать рабочий день',
                                     set_enabled=True)
                                 )


@dp.callback_query(Text(text_startswith='set_work_enabled_'))
async def cmd_set_workday(callback: types.CallbackQuery, state: FSMContext):
    workday_value = callback.data.split('_')[-1]

    if workday_value == '1' or workday_value == '0':
        workday = None
        if workday_value == '1':
            workday = grpc_calls.set_workday_status(
                user_id=callback.from_user.id,
                is_working=True
            )
        elif workday_value == '0':
            workday = grpc_calls.set_workday_status(
                user_id=callback.from_user.id,
                is_working=False
            )

        if workday.isWorking:
            await callback.message.edit_text(
                text='У вас сейчас рабочее время',
                reply_markup=factory.set_workday_keyboard(
                    text='Закончить рабочий день',
                    set_enabled=False)
            )
        else:
            await callback.message.edit_text(
                text='У вас сейчас отдых',
                reply_markup=factory.set_workday_keyboard(
                    text='Начать рабочий день',
                    set_enabled=True)
            )

        await callback.answer(text='Рабочий статус обновлен', show_alert=True)
    else:
        await callback.answer('Произошла ошибка, попробуйте еще раз')


@ dp.callback_query(Text(text_startswith='close_ticket'))
async def close_ticket(callback: types.CallbackQuery, state: FSMContext):
    ticketId = callback.data.split('_')[-1]
    userId = callback.from_user.id
    try:
        grpc_calls.close_ticket(ticketId)
        callback.answer(text='Тикет закрыт')
        # await bot.send_message(
        #     chat_id=userId,
        #     text='Тикет успешно закрыт')

        await state.set_state(MenuState.menu)
        await callback.message.delete()

    except grpc.RpcError as e:
        await bot.send_message(
            chat_id=callback.from_user.id,
            text='Произошла ошибка при закрытии тикета.' +
            'Используйте /start для перезагрузки бота'
        )
        pass


@ dp.callback_query(Text(text_startswith='loganswer'))
async def log_answer(callback: types.CallbackQuery, state: FSMContext):
    ticketId = callback.data.split('_')[-1]
    try:
        grpc_calls.log_agent_message(ticket_id=ticketId)
        keyboard = callback.message.reply_markup.inline_keyboard
        keyboard.pop()
        keyboard.append([factory.create_close_button(ticket_id=ticketId)])
        await callback.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

        await callback.answer(
            show_alert=True,
            text='Тикет помечен как отвеченный'
        )
    except Exception as e:
        await callback.answer(
            show_alert=True,
            text='Произошла ошибка, попробуйте еще раз'
        )


async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(check_available.main(bot=bot))
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
