from aiogram import Dispatcher, Bot, types
from aiogram.dispatcher.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, KICKED, LEFT, \
    RESTRICTED, MEMBER, ADMINISTRATOR, CREATOR
from aiogram.types import ChatMemberUpdated
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.fsm.context import FSMContext
import grpc
import sub_unsub_pb2_grpc
import sub_unsub_pb2
import ticket_bot_pb2
import ticket_bot_pb2_grpc
import administration
from settings import CHANNEL_ID, BOT_TOKEN
import asyncio
import messages


class SpamState(StatesGroup):
    spam = State()
    setup_join = State()
    setup_left = State()
    main = State()


dp = Dispatcher()
support_bot = Bot(token=BOT_TOKEN)


@dp.message(commands=["start"])
@dp.message(Text(text="Назад"))
async def cmd_start(message: types.Message, state: FSMContext):
    adminData = administration.getAdminById(str(message.from_user.id))

    if adminData is None:
        return

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text="Рассылка по подписчикам", callback_data="spam")],
        [types.InlineKeyboardButton(
            text="Настроить сообщение при подписке", callback_data="setup_join")],
        [types.InlineKeyboardButton(
            text="Настроить сообщение при отписке", callback_data="setup_left")],
    ])

    await state.set_state(SpamState.main)
    await support_bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)


@dp.callback_query(Text(text_startswith="setup_join"))
async def setup_join(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SpamState.setup_join)
    await support_bot.send_message(callback.message.chat.id, "Отправьте сообщения, которые вы хотели бы рассылать при подписке. Чтобы закончить отправьте: Exit.")
    messages_list = []

    @dp.message(SpamState.setup_join)
    async def send_spam(message: types.Message, state: FSMContext):
        message_id = message.message_id
        channel_id = message.chat.id

        if (message.text == "Exit"):
            messages.set_join_messages(messages=messages_list)
            messages_list.clear()
            await state.set_state(SpamState.main)
            await support_bot.send_message(message.chat.id, "Сообщение настроено!")
        else:
            messages_list.append(sub_unsub_pb2.SetAnnounceMessageRequest(
                channelId=str(channel_id),
                messageId=str(message_id)
            ))


@dp.callback_query(Text(text_startswith="setup_left"))
async def setup_left(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SpamState.setup_left)
    await support_bot.send_message(callback.message.chat.id, "Отправьте сообщения, которые вы хотели бы рассылать при отписке. Чтобы закончить отправьте: Exit.")
    messages_list = []

    @dp.message(SpamState.setup_left)
    async def send_spam(message: types.Message, state: FSMContext):
        message_id = message.message_id
        channel_id = message.chat.id

        if (message.text == "Exit"):
            messages.set_leave_messages(messages=messages_list)
            messages_list.clear()
            await state.set_state(SpamState.main)
            await support_bot.send_message(message.chat.id, "Сообщение настроено!")
        else:
            messages_list.append(sub_unsub_pb2.SetAnnounceMessageRequest(
                channelId=str(channel_id),
                messageId=str(message_id)
            ))


@dp.callback_query(Text(text_startswith="spam"))
async def spam(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SpamState.spam)
    await support_bot.send_message(callback.message.chat.id, "Составьте сообщение, которое вы бы хотели разослать:")

    @dp.message(SpamState.setup_left)
    async def send_spam(message: types.Message, state: FSMContext):
        message_id = message.message_id
        await state.set_state(SpamState.main)

    @dp.message(SpamState.spam)
    async def send_spam(message: types.Message):
        with grpc.insecure_channel('146.0.78.143:5001') as channel:
            stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
            request = sub_unsub_pb2.AdminChannelId(channelId=CHANNEL_ID)
            user_ids: sub_unsub_pb2.UserList = stub.GetChannelJoinList(request)
            await support_bot.send_message(message.chat.id, "Спам запущен")
            for user_id in user_ids.users:
                user_id: sub_unsub_pb2.UserIdRequest = user_id
                try:
                    await message.send_copy(chat_id=int(user_id.userId))
                except Exception as e:
                    continue
            await support_bot.send_message(message.chat.id, "Спам завершен")
            await state.set_state(SpamState.main)


@dp.chat_join_request_handler()
async def join_request(update: types.ChatJoinRequest):
    user_id = update.from_user.id
    # redirect_url = urllib.parse.quote_plus('https://t.me/TechSupport124313Bot')
    # keyboard = InlineKeyboardMarkup(inline_keyboard=[
    #     [types.InlineKeyboardButton(
    #         text="Техподдержка", url=f"http://146.0.78.143:3001/open?from={user_id}&to={redirect_url}")]
    # ], row_width=2)
    await update.approve()
    try:
        join_messages: sub_unsub_pb2.AnnounceMessagesResponse = messages.get_join_messages()

        for msg in join_messages.messages:
            await support_bot.copy_message(
                chat_id=user_id,
                from_chat_id=int(msg.channelId),
                message_id=int(msg.messageId)
            )
    except Exception:
        pass


@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=(KICKED | LEFT | RESTRICTED)
                                        <<
                                        (ADMINISTRATOR | CREATOR | MEMBER)))
async def left_message(event: ChatMemberUpdated):
    user_id = event.new_chat_member.user.id
    try:
        left_messages: sub_unsub_pb2.AnnounceMessagesResponse = messages.get_leave_messages()

        for msg in left_messages.messages:
            await support_bot.copy_message(
                chat_id=user_id,
                from_chat_id=int(msg.channelId),
                message_id=int(msg.messageId)
            )
    except Exception:
        pass

@dp.callback_query(Text(text_startswith="ts_request_announce"))
async def callbacks_num(callback: types.CallbackQuery):
    if callback.from_user.username is None:
        await callback.answer(
            text="Вам необходимо задать username для своего аккаунта в настройках telegram",
            show_alert=True)
        return

    try:
        with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
            stub = ticket_bot_pb2_grpc.TicketsStub(channel=grpc_channel)
            request = ticket_bot_pb2.ChannelId(channelId=CHANNEL_ID)
            callCenter = ticket_bot_pb2.CallcenterData = stub.GetCallcenterByChannelId(
                request)
            request = ticket_bot_pb2.OpenTicketRequest(
                userId=str(callback.from_user.id),
                channelId=CHANNEL_ID,
                callCenterId=callCenter.externalId,
                username=str(callback.from_user.username)
            )
            stub.OpenTicket(request)
    except grpc.RpcError as e:
        err_code = e.args[0].details
        if err_code == 'TOO_MANY_TICKETS':
            await callback.answer('Вы уже недавно обращались в поддержку.' +
                                    'Подождите перед тем как открывать запрос снова',
                                    show_alert=True)
            return

    await callback.answer("Спасибо за обращение! С вами скоро свяжутся.", show_alert=True)

async def main():
    await dp.start_polling(support_bot,
                           allowed_updates=dp.resolve_used_update_types())

if __name__ == '__main__':
    asyncio.run(main())
