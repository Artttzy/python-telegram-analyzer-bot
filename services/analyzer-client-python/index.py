import asyncio
import logging
import pyro
from aiogram import Bot, Dispatcher, types
import datetime
from datetime import timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.fsm.context import FSMContext
from handlers import user_join, user_leave
import grpc
import sub_unsub_pb2_grpc
import sub_unsub_pb2
import ticket_bot_pb2
import ticket_bot_pb2_grpc
import bot_manager_pb2
import bot_manager_pb2_grpc
import administration
import subscription_loop
from google.protobuf import timestamp_pb2
import msg_util
import urllib.parse
import pytz

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()
bot = Bot(token="5769910363:AAEvWdHotYX2stcYj44J4RlX7Xhocim99FQ")
dp.include_router(user_join.router)
dp.include_router(user_leave.router)


class MenuState(StatesGroup):
    menu = State()
    add_channel = State()
    all_stats = State()
    set_bots = State()
    post = State()
    post_text = State()
    post_link = State()
    poll = State()
    ts_post = State()
    ts_post_text = State()
    ts_post_link = State()
    spam = State()
    add_agent = State()
    delete_agent = State()
    add_centr = State()
    del_centr = State()
    add_spam = State()
    del_spam = State()
    add_admin = State()
    delete_admin = State()
    delete_channel = State()
    stats = State()
    join = State()
    left = State()


@dp.message(commands=["start"])
@dp.message(Text(text="Назад"))
async def cmd_start(message: types.Message, state: FSMContext):
    adminData = administration.getAdminById(str(message.from_user.id))

    if adminData is None:
        await message.reply('У вас недостаточно прав')
        return

    await state.set_state(MenuState.menu)

    buttons1 = [
        [
            types.KeyboardButton(text="Список админов 👮‍♂️"),
            types.KeyboardButton(text="Добавить админа ➕")
        ],
        [
            types.KeyboardButton(text="Список каналов 📄"),
            types.KeyboardButton(text="Добавить канал ➕")
        ]
    ]
    buttons2 = [
        [
            types.KeyboardButton(text="Список каналов 📄"),
            types.KeyboardButton(text="Добавить канал ➕")
        ]
    ]

    if adminData.superuser:
        buttons = ReplyKeyboardMarkup(keyboard=buttons1, resize_keyboard=True)
    else:
        buttons = types.ReplyKeyboardMarkup(
            keyboard=buttons2, resize_keyboard=True)

    await message.answer("Доброго времени суток! С чего вы хотели бы начать?", reply_markup=buttons)


@dp.message_handler(Text(text_startswith="Добавить админа"))
async def add_admin(message: types.Message, state: FSMContext):
    adminData = administration.getAdminById(str(message.from_user.id))

    if not adminData.superuser:
        await bot.send_message(message.chat.id, 'У вас недостаточно прав для этого действия')
        return

    await bot.send_message(message.chat.id, 'Пришлите username пользователя, которого вы хотели бы назначить администратором бота.')
    await state.set_state(MenuState.add_admin)

    @dp.message_handler(MenuState.add_admin)
    async def resolve(username: types.Message):
        userId = await pyro.resolve_username_to_user_id(username.text)
        request = sub_unsub_pb2.Admin(
            userId=str(userId),
            username=username.text,
            superuser=False)

        with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
            stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(grpc_channel)
            stub.AddAdmin(request=request)

        await bot.send_message(username.chat.id, await pyro.get_username_by_user_id(userId) + ' теперь админ.')
        await state.set_state(MenuState.menu)


@dp.message_handler(Text(text_startswith="Список админов"))
async def admins(message: types.Message, state: FSMContext):
    adminData = administration.getAdminById(str(message.from_user.id))
    if not adminData.superuser:
        await bot.send_message(message.chat.id, 'У вас недостаточно прав для этого действия')
        return

    keyboard = [
        [types.KeyboardButton(text="Удалить админа")],
        [types.KeyboardButton(text="Назад")]
    ]

    with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(grpc_channel)
        request = sub_unsub_pb2.EmptyMessage()
        response: sub_unsub_pb2.AdminList = stub.GetAdmins(request=request)

        for admin in response.admins:
            button = types.KeyboardButton(text=admin.username)
            keyboard.insert(0, [button])

    buttons = types.ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True)
    await bot.send_message(message.chat.id, "Список админов:", reply_markup=buttons)


@dp.message_handler(Text(text_startswith="Удалить админа"))
async def delete_admin(message: types.Message, state: FSMContext):
    adminData = administration.getAdminById(str(message.from_user.id))
    if not adminData.superuser:
        await bot.send_message(message.chat.id, 'У вас недостаточно прав для этого действия')
        return
    await bot.send_message(message.chat.id, 'Выберите админа для удаления')
    await state.set_state(MenuState.delete_admin)

    @dp.message(MenuState.delete_admin)
    async def delete_adm(username: types.Message):
        with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
            stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(grpc_channel)
            request = sub_unsub_pb2.Admin(userId=str(await pyro.resolve_username_to_user_id(username=username.text)))
            response: sub_unsub_pb2.EmptyMessage = stub.RemoveAdmin(request)
            await bot.send_message(message.chat.id, 'Админ успешно удален!')
        await state.set_state(MenuState.menu)


@dp.message_handler(Text(text_startswith="Добавить канал"))
async def add_channel(message: types.Message, state: FSMContext):
    adminData = administration.getAdminById(str(message.from_user.id))

    if adminData is None:
        await message.reply('У вас недостаточно прав')
        return

    await bot.send_message(message.chat.id, 'Перешлите любое сообщение из канала, в котором бот является администратором')
    await state.set_state(MenuState.add_channel)

    @dp.message(MenuState.add_channel)
    async def check_channel(forwarded: types.Message):
        channel = forwarded.forward_from_chat
        bot_member = await bot.get_chat_member(channel.id, bot.id)
        if (bot_member.status == "administrator"):
            with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
                stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(grpc_channel)
                request = sub_unsub_pb2.AdminChannel(
                    channelId=str(channel.id),
                    channelName=channel.title
                )

                stub.SetAdminChannel(request=request)

            await bot.send_message(message.chat.id, 'Бот администратор канала!')
        else:
            await bot.send_message(message.chat.id, 'Бот не является администратором канала!')
        await state.set_state(MenuState.menu)


@dp.message_handler(Text(text_startswith="Список каналов"))
async def get_channels(message: types.Message, state: FSMContext):
    adminData = administration.getAdminById(str(message.from_user.id))

    if adminData is None:
        await message.reply('У вас недостаточно прав')
        return
    elif adminData.superuser:
        keyboard = [
            [types.KeyboardButton(text="Удалить канал")],
            [types.KeyboardButton(text="Назад")]
        ]
    else:
        keyboard = [
            [types.KeyboardButton(text="Назад")]
        ]

    with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(grpc_channel)
        request = sub_unsub_pb2.EmptyMessage()
        response: sub_unsub_pb2.AdminChannelList = stub.GetAdminChannels(
            request=request)

        for admin_channel in response.channels:
            button = types.KeyboardButton(
                text=f"Канал: {admin_channel.channelName}::{admin_channel.channelId}")
            keyboard.insert(0, [button])

    buttons = types.ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True)
    await bot.send_message(message.chat.id, "Список каналов:", reply_markup=buttons)


@dp.message_handler(Text(text_startswith="Удалить канал"))
async def delete_channel(message: types.Message, state: FSMContext):
    adminData = administration.getAdminById(str(message.from_user.id))
    if not adminData.superuser:
        await message.reply('У вас недостаточно прав')
        return

    await bot.send_message(message.chat.id, 'Перешлите любое сообщение из канала:')
    await state.set_state(MenuState.delete_channel)

    @dp.message(MenuState.delete_channel)
    async def delete_chnl(forwarded: types.Message):
        with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
            stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(grpc_channel)
            request = sub_unsub_pb2.AdminChannelId(
                channelId=str(forwarded.forward_from_chat.id))
            response: sub_unsub_pb2.EmptyMessage = stub.DeleteAdminChannel(
                request)
            await bot.send_message(message.chat.id, 'Канал успешно удален!')
        await state.set_state(MenuState.menu)


@dp.message_handler(Text(text_startswith="Канал: "))
async def channel_actions(message: types.Message, state: FSMContext):
    adminData = administration.getAdminById(str(message.from_user.id))

    if adminData is None:
        await message.reply('У вас недостаточно прав')
        return
    data = message.text.split("::")
    channelId = data[len(data) - 1]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text="Общая статистика", callback_data="cmd_all_" + channelId)],
        [types.InlineKeyboardButton(
            text="Детальная статистика", callback_data="cmd_det_" + channelId)],
        [types.InlineKeyboardButton(
            text="Действия", callback_data="cmd_act_" + channelId)],
        [types.InlineKeyboardButton(
            text="Выход", callback_data="cmd_10_" + channelId)]
    ])
    await bot.send_message(message.chat.id, "Выберите желаемую информацию об этом канале.", reply_markup=keyboard)


@dp.callback_query(Text(text_startswith="cmd_"))
async def callbacks_num(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    channelId = data[2]
    action = data[1]

    if action == "1":
        text = "<u><b>Количество подписчиков по датам:</b></u>\n\n"
        with grpc.insecure_channel('146.0.78.143:5001') as channel:
            stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
            request = sub_unsub_pb2.AdminChannelId(channelId=channelId)
            stats: sub_unsub_pb2.SubscriberHistory = stub.GetSubscriberHistory(
                request)
            for stat in stats.history:
                text += f"{stat.date}: {stat.value}\n"
        await bot.send_message(callback.message.chat.id, text=text, parse_mode="HTML")

    elif action == "2":
        await state.set_state(MenuState.join)
        await state.update_data(channel_id=channelId)
        await bot.send_message(callback.message.chat.id, "Введите дату в формате дд-мм-гггг")

        @dp.message(MenuState.join)
        async def request(mg: types.Message, state: FSMContext):
            chat_data = await state.get_data()
            channel_id = chat_data.get("channel_id")
            text = mg.text
            ans = "<u><b>Количество подписавшихся за дату по часам:</b></u>\n\n"
            format = "%d-%m-%Y"
            date = None
            try:
                date = datetime.datetime.strptime(text, format)
            except:
                await bot.send_message(mg.chat.id, "Вы ввели дату в неправильном формате!")
                return
            with grpc.insecure_channel('146.0.78.143:5001') as channel:
                stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
                timestamp = timestamp_pb2.Timestamp()
                timestamp.FromDatetime(date)

                request = sub_unsub_pb2.JoinLeftRequest(
                    day=timestamp, channelId=channel_id)
                stats: sub_unsub_pb2.JoinLeftStatisticsResponse = stub.JoinLeftStatistics(
                    request)
                for stat in stats.joined:
                    ans += f"{stat.time}    :    +{stat.value}\n"

                await bot.send_message(mg.chat.id, text=ans, parse_mode="HTML")
                await state.set_state(MenuState.menu)

    elif action == "3":
        await state.set_state(MenuState.left)
        await state.update_data(channel_id=channelId)
        await bot.send_message(callback.message.chat.id, "Введите дату в формате дд-мм-гггг")

        @dp.message(MenuState.left)
        async def request(mg: types.Message):
            chat_data = await state.get_data()
            channel_id = chat_data.get("channel_id")
            ans = "<u><b>Количество отписавшихся за дату по часам:</b></u>\n\n"
            text = mg.text
            format = "%d-%m-%Y"
            date = None
            try:
                date = datetime.datetime.strptime(text, format)
            except:
                await bot.send_message(mg.chat.id, "Вы ввели дату в неправильном формате!")
                return
            with grpc.insecure_channel('146.0.78.143:5001') as channel:
                stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
                timestamp = timestamp_pb2.Timestamp()
                timestamp.FromDatetime(date)

                request = sub_unsub_pb2.JoinLeftRequest(
                    day=timestamp, channelId=channel_id)
                stats: sub_unsub_pb2.JoinLeftStatisticsResponse = stub.JoinLeftStatistics(
                    request)
                for stat in stats.left:
                    ans += f"{stat.time}    :    -{stat.value}\n"

                await bot.send_message(mg.chat.id, text=ans, parse_mode="HTML")
                await state.set_state(MenuState.menu)

    elif action == "4":
        ans = "<u><b>Количество просмотров на постах по датам:</b></u>\n\n"
        zone = pytz.timezone('Asia/Almaty')

        with grpc.insecure_channel('146.0.78.143:5001') as channel:
            stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
            request = sub_unsub_pb2.AdminChannelId(channelId=channelId)
            messages: sub_unsub_pb2.ChannelMessageList = stub.GetMessages(
                request)
            today = datetime.datetime.now(tz=zone)
            today = today.replace(hour=0, minute=0, second=0,
                                  microsecond=0)

            for day in (today - timedelta(days=n) for n in range(0, 14 - 1)):
                day = day.replace(tzinfo=zone)
                nextDay = day + timedelta(days=1)
                nextDay = nextDay.replace(tzinfo=zone)
                message_ids: list[int] = list(msg_util.message_ids_in_range(
                    messages=messages, start=day, end=nextDay))
                views = await pyro.get_message_views(channelId=channelId, messageids=message_ids)
                ans += f"{str(day).split(' ')[0]} : Среднее: {round(views[0], 2)}; Суммарное: {views[1]}\n"
            await bot.send_message(callback.message.chat.id, text=ans, parse_mode="HTML")

    elif action == "5":
        ans = "<u><b>Среднее количество реакций на постах по датам:</b></u>\n\n"
        zone = pytz.timezone('Asia/Almaty')
        # TODO: Войти в аккаунт заказчика
        with grpc.insecure_channel('146.0.78.143:5001') as channel:
            stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
            request = sub_unsub_pb2.AdminChannelId(channelId=channelId)
            messages: sub_unsub_pb2.ChannelMessageList = stub.GetMessages(
                request)
            today = datetime.datetime.now(tz=zone)
            today = today.replace(hour=0, minute=0, second=0,
                                  microsecond=0)

            for day in (today - timedelta(days=n) for n in range(0, 14 - 1)):
                day = day.replace(tzinfo=zone)
                nextDay = day + timedelta(days=1)
                nextDay = nextDay.replace(tzinfo=zone)
                message_ids: list[int] = list(msg_util.message_ids_in_range(
                    messages=messages, start=day, end=nextDay))
                reactions = await pyro.get_message_reactions_by_user(channelId=channelId, messageids=message_ids)
                ans += f"{str(day).split(' ')[0]} : Среднее: {round(reactions[0], 2)}; Суммарное: {round(reactions[1], 2)}\n"
            await bot.send_message(callback.message.chat.id, text=ans, parse_mode="HTML")

    elif action == "all":
        
        await bot.send_message(callback.message.chat.id, text="Введите дату в формате дд-мм-гггг:")
        await state.set_state(MenuState.all_stats)
        @dp.message(MenuState.all_stats)
        async def all_stats(message: types.Message, state: FSMContext):
            zone = pytz.timezone('Asia/Almaty')
            try:
                date = datetime.datetime.strptime(message.text, "%d-%m-%Y").astimezone(tz=zone)
            except:
                await bot.send_message(message.chat.id, "Вы ввели дату в неправильном формате!")
                return
            ans = f"__*Общая статистика по каналу за дату:*__ \n\n"
            ans += "_Количество подписчиков:_ "
            with grpc.insecure_channel('146.0.78.143:5001') as channel:
                stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
                request = sub_unsub_pb2.AdminChannelId(channelId=channelId)
                stats: sub_unsub_pb2.SubscriberHistory = stub.GetSubscriberHistory(
                    request)
                temp = date.strftime("%Y-%m-%d")
                for stat in stats.history:
                    if (stat.date == temp):
                        ans += f"{stat.value}\n"
                        break
            ans += "_Количество подписавшихся:_ \+"
            with grpc.insecure_channel('146.0.78.143:5001') as channel:
                stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
                date = date + timedelta(hours=12)
                timestamp = timestamp_pb2.Timestamp()
                timestamp.FromDatetime(date)
                join = 0
                left = 0
                request = sub_unsub_pb2.JoinLeftRequest(
                    day=timestamp, channelId=channelId)
                stats: sub_unsub_pb2.JoinLeftStatisticsResponse = stub.JoinLeftStatistics(
                    request)
                for stat in stats.joined:
                    join += stat.value
                for stat in stats.left:
                    left += stat.value
            ans += f"{join}\n"
            ans += "_Количество отписавшихся:_ \-"
            ans += f"{left}\n\n"
            ans += "_Суммарное количество просмотров: _"
            zone = pytz.timezone('Asia/Almaty')

            with grpc.insecure_channel('146.0.78.143:5001') as channel:
                stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
                request = sub_unsub_pb2.AdminChannelId(channelId=channelId)
                messages: sub_unsub_pb2.ChannelMessageList = stub.GetMessages(
                    request)
                today = date
                today = today.replace(hour=0, minute=0, second=0, microsecond=0)
                nextDay = today + timedelta(days=1)
                message_ids: list[int] = list(msg_util.message_ids_in_range(
                    messages=messages, start=today, end=nextDay))
                views = await pyro.get_message_views(channelId=channelId, messageids=message_ids)
                ans += f"{views[1]}\n_Среднее количество просмотров на посте:_ {round(views[0], 2)}\n\n"

            ans += "_Суммарное количество реакций:_ "
            with grpc.insecure_channel('146.0.78.143:5001') as channel:
                stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
                request = sub_unsub_pb2.AdminChannelId(channelId=channelId)
                messages: sub_unsub_pb2.ChannelMessageList = stub.GetMessages(
                    request)
                today = date
                today = today.replace(hour=0, minute=0, second=0, microsecond=0)
                nextDay = today + timedelta(days=1)
                message_ids: list[int] = list(msg_util.message_ids_in_range(
                    messages=messages, start=today, end=nextDay))
                reactions = await pyro.get_message_reactions_by_user(channelId=channelId, messageids=message_ids)
                ans += f"{reactions[1]}\n_Среднее количество реакций на посте:_ {round(reactions[0], 2)}\n\n"

            ans += "__Количество тикетов техподдержки:__ "
            with grpc.insecure_channel('146.0.78.143:5001') as channel:
                day = timestamp_pb2.Timestamp()
                day.FromDatetime(date)
                stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
                request = sub_unsub_pb2.TicketStatsRequest(
                    day=day,
                    channelId=channelId
                )
                avg_time: sub_unsub_pb2.AnswerTime = stub.GetAverageAnswerTime(
                    request)

                avg_time_dt = datetime.datetime.fromtimestamp(avg_time.answerTime.seconds + avg_time.answerTime.nanos/1e9,
                                                            tz=datetime.timezone.utc)
                ans += f"{avg_time.ticketCount}\n"
                ans += "__Среднее время ответа агентов поддержки:__ \n"
                ans += f"{avg_time_dt.hour} часов {avg_time_dt.minute} минут {avg_time_dt.second} секунд\n\n"

            with grpc.insecure_channel('146.0.78.143:5001') as channel:
                gender = [0, 0]
                age = [0, 0, 0, 0, 0]
                stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
                request = sub_unsub_pb2.AdminChannelId(channelId=channelId)
                stats: sub_unsub_pb2.CAStats = stub.GetStatsPerChannel(request)
                for stat in stats.stats:
                    if (stat.gender == 'male'):
                        gender[0] += 1
                    elif (stat.gender == 'female'):
                        gender[1] += 1

                    if (stat.age == 18):
                        age[0] += 1
                    elif (stat.age == 25):
                        age[1] += 1
                    elif (stat.age == 33):
                        age[2] += 1
                    elif (stat.age == 42):
                        age[3] += 1
                    elif (stat.age == 50):
                        age[4] += 1
                if (gender[0] == 0 and gender[1] == 0):
                    ans += "__Пол аудитории:__ \n"
                    ans += f"🚹: 0%\n"
                    ans += f"🚺: 0%\n\n"
                else:
                    ans += "__Пол аудитории:__ \n"
                    ans += f"🚹: {round((gender[0] * 100)/(gender[0] + gender[1]), 2)}%\n"
                    ans += f"🚺: {round((gender[1] * 100)/(gender[0] + gender[1]), 2)}%\n\n"

                temp = 0
                for i in age:
                    temp += i
                if (temp == 0):
                    ans += "__Возраст аудитории:__ \n"
                    ans += f"• 18\-24: 0%\n"
                    ans += f"• 25\-32: 0%\n"
                    ans += f"• 33\-41: 0%\n"
                    ans += f"• 42\-50: 0%\n"
                    ans += f"• 50\+: 0%\n"
                else:
                    ans += "__Возраст аудитории:__ \n"
                    ans += f"• 18\-24: {round((age[0] * 100)/(temp), 2)}%\n"
                    ans += f"• 25\-32: {round((age[1] * 100)/(temp), 2)}%\n"
                    ans += f"• 33\-41: {round((age[2] * 100)/(temp), 2)}%\n"
                    ans += f"• 42\-50: {round((age[3] * 100)/(temp), 2)}%\n"
                    ans += f"• 50\+: {round((age[4] * 100)/(temp), 2)}%\n"

            ans = str.replace(ans, '.', '\.')
            await bot.send_message(callback.message.chat.id, text=ans, parse_mode="MarkdownV2")
            await state.set_state(MenuState.menu)

    elif action == "8":
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Разместить пост с кнопкой-ссылкой", callback_data="cmd_linkbutton_" + channelId)],
            [types.InlineKeyboardButton(
                text="Разместить пост с кнопкой-запросом в техподдержку", callback_data="cmd_tsbutton_" + channelId)],
            [types.InlineKeyboardButton(
                text="Назад", callback_data="cmd_back_" + channelId)]
        ])
        await callback.message.edit_reply_markup(reply_markup=keyboard)

    elif action == "tsbutton":
        await bot.send_message(callback.message.chat.id, "Составьте сообщение, которое вы бы хотели запостить:")
        post_det = []
        await state.set_state(MenuState.ts_post)
        await state.update_data(channel_id=channelId)


        @dp.message(MenuState.ts_post)
        async def ts_post(post: types.Message, state: FSMContext):
            chat_data = await state.get_data()
            channel_id = chat_data.get("channel_id")
            post_det.clear()
            post_det.append(post)
            await bot.send_message(post.chat.id, "Отправьте текст кнопки")
            await state.set_state(MenuState.ts_post_text)
            await state.update_data(channel_id=channel_id)

            @dp.message(MenuState.ts_post_text)
            async def ts_post_text(msg: types.Message, state: FSMContext):
                chat_data = await state.get_data()
                channel_id = chat_data.get("channel_id")
                post_det.append(msg.text)
                keyboard = [[
                    InlineKeyboardButton(
                        text=post_det[1], callback_data="cmd_tsrequest_" + channel_id)
                ]]
                new_post = await post_det[0].send_copy(channel_id, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
                with grpc.insecure_channel('46.17.100.129:5001') as grpc_channel:
                    stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(
                        grpc_channel)
                    request = sub_unsub_pb2.SaveMessageRequest(
                        channelId=channel_id,
                        messageId=str(new_post.message_id)
                    )

                    stub.SaveMessage(request)
                    await state.set_state(MenuState.menu)

    elif action == "tsrequest":
        if callback.from_user.username is None:
            await callback.answer(
                text="Вам необходимо задать username для своего аккаунта в настройках telegram",
                show_alert=True)
            return

        try:
            with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
                stub = ticket_bot_pb2_grpc.TicketsStub(channel=grpc_channel)
                request = ticket_bot_pb2.ChannelId(channelId=channelId)
                callCenter = ticket_bot_pb2.CallcenterData = stub.GetCallcenterByChannelId(
                    request)
                request = ticket_bot_pb2.OpenTicketRequest(
                    userId=str(callback.from_user.id),
                    channelId=channelId,
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

    elif action == "linkbutton":
        await bot.send_message(callback.message.chat.id, "Составьте сообщение, которое вы бы хотели запостить:")
        post_det = []
        await state.set_state(MenuState.post)
        await state.update_data(channel_id=channelId)

        @dp.message(MenuState.post)
        async def post(post: types.Message, state: FSMContext):
            chat_data = await state.get_data()
            channel_id = chat_data.get("channel_id")
            post_det.clear()
            post_det.append(post)
            await bot.send_message(post.chat.id, "Отправьте текст кнопки")
            await state.set_state(MenuState.post_text)
            await state.update_data(channel_id=channel_id)

            @dp.message(MenuState.post_text)
            async def post_text(msg: types.Message, state: FSMContext):
                chat_data = await state.get_data()
                channel_id = chat_data.get("channel_id")
                post_det.append(msg.text)
                await bot.send_message(msg.chat.id, "Отправьте ссылку кнопки")
                await state.set_state(MenuState.post_link)
                await state.update_data(channel_id=channel_id)

                @dp.message(MenuState.post_link)
                async def post_link(link: types.Message, state: FSMContext):
                    chat_data = await state.get_data()
                    channel_id = chat_data.get("channel_id")
                    link = link.text
                    redirect_url = urllib.parse.quote_plus(link)
                    keyboard = [[
                        InlineKeyboardButton(
                            text=post_det[1], url=f"http://146.0.78.143:3001/open?from={channelId}&to={redirect_url}")
                    ]]
                    new_post = await post_det[0].send_copy(channel_id, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
                    with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
                        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(
                            grpc_channel)
                        request = sub_unsub_pb2.SaveMessageRequest(
                            channelId=channel_id,
                            messageId=str(new_post.message_id)
                        )

                        stub.SaveMessage(request)
                        await state.set_state(MenuState.menu)

    elif action == "9":
        await state.set_state(MenuState.poll)
        keyboard1 = InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="1. Укажите свой пол:", callback_data="ans_1")],
            [
                types.InlineKeyboardButton(
                    text="Мужской", callback_data="poll_gender_male"),
                types.InlineKeyboardButton(
                    text="Женский", callback_data="poll_gender_female")
            ],
            [types.InlineKeyboardButton(
                text="2. Укажите свой возраст:", callback_data="ans_2")],
            [
                types.InlineKeyboardButton(
                    text="18-24", callback_data="poll_age_18"),
                types.InlineKeyboardButton(
                    text="25-32", callback_data="poll_age_25"),
                types.InlineKeyboardButton(
                    text="33-41", callback_data="poll_age_33"),
                types.InlineKeyboardButton(
                    text="42-50", callback_data="poll_age_42"),
                types.InlineKeyboardButton(
                    text="50+", callback_data="poll_age_50")
            ]
        ])

        new_post = await bot.send_message(channelId, """*ОПРОС:*""", reply_markup=keyboard1, parse_mode="Markdown")
        await state.set_state(MenuState.menu)
        with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
            stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(grpc_channel)
            request = sub_unsub_pb2.SaveMessageRequest(
                channelId=channelId,
                messageId=str(new_post.message_id)
            )

            stub.SaveMessage(request)

    elif action == "det":
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Количество подписчиков ", callback_data="cmd_1_" + channelId)],
            [types.InlineKeyboardButton(
                text="Количество подписавшихся", callback_data="cmd_2_" + channelId)],
            [types.InlineKeyboardButton(
                text="Количество отписавшихся", callback_data="cmd_3_" + channelId)],
            [types.InlineKeyboardButton(
                text="Среднее количество просмотров", callback_data="cmd_4_" + channelId)],
            [types.InlineKeyboardButton(
                text="Среднее количество реакций", callback_data="cmd_5_" + channelId)],
            [types.InlineKeyboardButton(
                text="Среднее время ответа агентов техподдержки", callback_data="cmd_avgtime_" + channelId)],
            [types.InlineKeyboardButton(
                text="Количество id юзеров", callback_data="cmd_idcount_" + channelId)],
            [types.InlineKeyboardButton(
                text="Назад", callback_data="cmd_back_" + channelId)]
        ])
        await callback.message.edit_reply_markup(reply_markup=keyboard)

    elif action == "idcount":
        ans = "Количество собранных id: "
        with grpc.insecure_channel('146.0.78.143:5001') as channel:
            stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
            request = sub_unsub_pb2.AdminChannelId(channelId=channelId)
            user_ids: sub_unsub_pb2.UserList = stub.GetChannelJoinList(request)
            ans += str(len(user_ids.users))
            await bot.send_message(callback.message.chat.id, ans)

    elif action == "avgtime":
        ans = "__*Статистика по времени ответа агентов по датам:*__\n\n"
        with grpc.insecure_channel('146.0.78.143:5001') as channel:
            day = timestamp_pb2.Timestamp()
            day.FromDatetime(datetime.datetime.now(tz=datetime.timezone.utc))
            stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
            request = sub_unsub_pb2.TicketStatsRequest(
                day=day,
                channelId=channelId
            )
            answer_stats: sub_unsub_pb2.DayAnswerStats = stub.GetAnswerTimeForEach(
                request)

            zone = pytz.timezone('Asia/Almaty')
            for stat in reversed(answer_stats.stats):
                dt = datetime.datetime.fromtimestamp(stat.day.seconds + stat.day.nanos/1e9,
                                                     tz=zone)
                ans += f"_{dt.date()}_\n"
                for agent in stat.stats:
                    avg_time_dt = datetime.datetime.fromtimestamp(agent.answerTime.seconds + agent.answerTime.nanos/1e9,
                                                                  tz=datetime.timezone.utc)
                    ans += f"@{await pyro.get_username_by_user_id(int(agent.userId))}:" +\
                        f"Тикетов: {agent.ticketCount}; Среднее время ответа: {avg_time_dt.hour} часов " +\
                        f"{avg_time_dt.minute} минут {avg_time_dt.second} секунд\n"
                ans += "\n\n"
            await bot.send_message(callback.message.chat.id, ans, parse_mode="Markdown")

    elif action == "act":
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Разместить пост с кнопкой", callback_data="cmd_8_" + channelId)],
            [types.InlineKeyboardButton(
                text="Разместить опрос для сбора данных о ЦА", callback_data="cmd_9_" + channelId)],
            [types.InlineKeyboardButton(
                text="Настроить бота для анонсов", callback_data="cmd_ann_" + channelId)],
            [types.InlineKeyboardButton(
                text="Настроить бота для техподдержки", callback_data="cmd_ts_" + channelId)],
            [types.InlineKeyboardButton(
                text="Назад", callback_data="cmd_back_" + channelId)]
        ])
        await callback.message.edit_reply_markup(reply_markup=keyboard)

    elif action == "ann":
        adminData = administration.getAdminById(str(callback.from_user.id))
        if not adminData.superuser:
            await callback.message.reply('У вас недостаточно прав')
            return
        try:
            with grpc.insecure_channel('146.0.78.143:5001') as channel:
                stub = ticket_bot_pb2_grpc.TicketsStub(channel=channel)
                request = ticket_bot_pb2.ChannelId(channelId=channelId)
                exists: ticket_bot_pb2.AnnouneBotExists = stub.GetAnounceBotByChannelId(
                    request)
            if exists.exists:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="Удалить анонс-бота", callback_data="cmd_delspam_" + channelId)],
                    [types.InlineKeyboardButton(
                        text="Назад", callback_data="cmd_back_" + channelId)]
                ])
                await callback.message.edit_text("Анонс-бот найден:")
                await callback.message.edit_reply_markup(reply_markup=keyboard)
            else:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="Добавить анонс-бота", callback_data="cmd_addspam_" + channelId)],
                    [types.InlineKeyboardButton(
                        text="Назад", callback_data="cmd_back_" + channelId)]
                ])
                await callback.message.edit_text("Анонс-бот не найден:")
                await callback.message.edit_reply_markup(reply_markup=keyboard)
        except grpc.RpcError as e:
            pass

    elif action == "addspam":
        adminData = administration.getAdminById(str(callback.from_user.id))
        if not adminData.superuser:
            await callback.message.reply('У вас недостаточно прав')
            return
        await bot.send_message(chat_id=int(adminData.userId), text="Отправьте токен бота, которого вы бы хотели назначить анонс-ботом для канала")
        await state.set_state(MenuState.add_spam)
        await state.update_data(channel_id=channelId)

        @dp.message(MenuState.add_spam)
        async def add_spam(token: types.Message, state: FSMContext):
            chat_data = await state.get_data()
            channel_id = chat_data.get("channel_id")
            try:
                with grpc.insecure_channel('146.0.78.143:5001') as channel:
                    stub = ticket_bot_pb2_grpc.TicketsStub(channel=channel)
                    request = ticket_bot_pb2.RegisterCallcenterRequest(
                        channelId=channel_id)
                    ticket_bot_pb2.Empty = stub.AddAnnounceBot(
                        request)
            except Exception as e:
                pass

            try:
                with grpc.insecure_channel('146.0.78.143:40001') as channel:
                    stub = bot_manager_pb2_grpc.BotManagerStub(channel=channel)
                    request = bot_manager_pb2.CreateSpamBotRequest(
                        bot_token=token.text, bot_channel_id=channel_id)
                    stub.CreateSpamBot(request)
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(
                            text="Удалить анонс-бота", callback_data="cmd_delspam_" + channel_id)],
                        [types.InlineKeyboardButton(
                            text="Назад", callback_data="cmd_back_" + channel_id)]
                    ])
                    await callback.message.edit_text("Анонс-бот найден:")
                    await callback.message.edit_reply_markup(reply_markup=keyboard)
            except Exception as e:
                pass

            await state.set_state(MenuState.menu)

    elif action == "delspam":
        adminData = administration.getAdminById(str(callback.from_user.id))
        if not adminData.superuser:
            await callback.message.reply('У вас недостаточно прав')
            return
        await bot.send_message(chat_id=int(adminData.userId), text="Отправьте токен бота, который является анонс-ботом для канала")
        await state.set_state(MenuState.del_spam)
        await state.update_data(channel_id=channelId)

        @dp.message(MenuState.del_spam)
        async def del_spam(token: types.Message, state: FSMContext):
            chat_data = await state.get_data()
            channel_id = chat_data.get("channel_id")
            try:
                with grpc.insecure_channel('146.0.78.143:5001') as channel:
                    stub = ticket_bot_pb2_grpc.TicketsStub(channel=channel)
                    request = ticket_bot_pb2.ChannelId(channelId=channel_id)
                    ticket_bot_pb2.Empty = stub.RemoveAnnounceBot(
                        request)
            except Exception as e:
                pass

            try:
                with grpc.insecure_channel('146.0.78.143:40001') as channel:
                    stub = bot_manager_pb2_grpc.BotManagerStub(channel=channel)
                    request = bot_manager_pb2.DeleteBotRequest(
                        bot_token=token.text)
                    stub.DeleteBot(request)
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [types.InlineKeyboardButton(
                            text="Добавить анонс-бота", callback_data="cmd_addspam_" + channel_id)],
                        [types.InlineKeyboardButton(
                            text="Назад", callback_data="cmd_back_" + channel_id)]
                    ])
                    await callback.message.edit_text("Анонс-бот не найден:")
                    await callback.message.edit_reply_markup(reply_markup=keyboard)
            except Exception as e:
                pass

            await state.set_state(MenuState.menu)

    elif action == "ts":
        adminData = administration.getAdminById(str(callback.from_user.id))
        if not adminData.superuser:
            await callback.message.reply('У вас недостаточно прав')
            return

        try:
            with grpc.insecure_channel('146.0.78.143:5001') as channel:
                stub = ticket_bot_pb2_grpc.TicketsStub(channel=channel)
                request = ticket_bot_pb2.ChannelId(channelId=channelId)
                callCenter: ticket_bot_pb2.CallcenterData = stub.GetCallcenterByChannelId(
                    request)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="Настроить колл-центр", callback_data="cmd_setcentr_" + channelId)],
                [types.InlineKeyboardButton(
                    text="Удалить колл-центр", callback_data="cmd_delcentr_" + channelId)],
                [types.InlineKeyboardButton(
                    text="Назад", callback_data="cmd_back_" + channelId)]
            ])
            await callback.message.edit_text("Колл-центр найден:")
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except grpc.RpcError as e:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="Добавить колл-центр", callback_data="cmd_addcentr_" + channelId)],
                [types.InlineKeyboardButton(
                    text="Назад", callback_data="cmd_back_" + channelId)]
            ])
            await callback.message.edit_text("Колл-центр не найден:")
            await callback.message.edit_reply_markup(reply_markup=keyboard)

    elif action == "setcentr":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Список агентов", callback_data="cmd_getagents_" + channelId)],
            [types.InlineKeyboardButton(
                text="Добавить агента", callback_data="cmd_addagent_" + channelId)],
            [types.InlineKeyboardButton(
                text="Удалить агента", callback_data="cmd_delagent_" + channelId)],
            [types.InlineKeyboardButton(
                text="Назад", callback_data="cmd_back_" + channelId)]
        ])
        await callback.message.edit_text("Настройка колл-центра:")
        await callback.message.edit_reply_markup(reply_markup=keyboard)

    elif action == "getagents":
        adminData = administration.getAdminById(str(callback.from_user.id))
        if not adminData.superuser:
            await callback.message.reply('У вас недостаточно прав')
            return
        ans = "Список агентов:\n"
        with grpc.insecure_channel('146.0.78.143:5001') as channel:
            stub = ticket_bot_pb2_grpc.TicketsStub(channel=channel)
            request = ticket_bot_pb2.ChannelId(channelId=channelId)
            callCenter: ticket_bot_pb2.CallcenterData = stub.GetCallcenterByChannelId(
                request)
            for agent in callCenter.agents:
                ans += f"@{await pyro.get_username_by_user_id(int(agent.userId))}\n"
            await bot.send_message(chat_id=int(adminData.userId), text=ans)

    elif action == "addagent":
        adminData = administration.getAdminById(str(callback.from_user.id))
        if not adminData.superuser:
            await callback.message.reply('У вас недостаточно прав')
            return
        await bot.send_message(chat_id=int(adminData.userId), text="Отправьте юзернейм пользователя, которого вы бы хотели назначить агентом тех-поддержки для канала")
        await state.set_state(MenuState.add_agent)
        await state.update_data(channel_id=channelId)

        @dp.message(MenuState.add_agent)
        async def add_agent(username: types.Message, state: FSMContext):
            chat_data = await state.get_data()
            channel_id = chat_data.get("channel_id")
            user_id = await pyro.resolve_username_to_user_id(username=username.text)
            try:
                with grpc.insecure_channel('146.0.78.143:5001') as channel:
                    stub = ticket_bot_pb2_grpc.TicketsStub(channel=channel)
                    request = ticket_bot_pb2.EditAgentRequest(channel=ticket_bot_pb2.ChannelId(
                        channelId=channel_id), agent=ticket_bot_pb2.AgentData(userId=str(user_id)))
                    callCenter: ticket_bot_pb2.Empty = stub.AddAgent(request)
                    await state.set_state(MenuState.menu)
                    await bot.send_message(username.chat.id, text="Агент добавлен.")
            except Exception as e:
                pass

    elif action == "delagent":
        adminData = administration.getAdminById(str(callback.from_user.id))
        if not adminData.superuser:
            await callback.message.reply('У вас недостаточно прав')
            return
        await bot.send_message(chat_id=int(adminData.userId), text="Отправьте юзернейм пользователя, которого вы бы хотели назначить агентом тех-поддержки для канала")
        await state.set_state(MenuState.delete_agent)
        await state.update_data(channel_id=channelId)

        @dp.message(MenuState.delete_agent)
        async def delete_agent(username: types.Message, state: FSMContext):
            chat_data = await state.get_data()
            channel_id = chat_data.get("channel_id")
            user_id = await pyro.resolve_username_to_user_id(username=username.text)
            try:
                with grpc.insecure_channel('146.0.78.143:5001') as channel:
                    stub = ticket_bot_pb2_grpc.TicketsStub(channel=channel)
                    request = ticket_bot_pb2.EditAgentRequest(channel=ticket_bot_pb2.ChannelId(
                        channelId=channel_id), agent=ticket_bot_pb2.AgentData(userId=str(user_id)))
                    callCenter: ticket_bot_pb2.Empty = stub.RemoveAgent(
                        request)
                    await state.set_state(MenuState.menu)
                    await bot.send_message(username.chat.id, text="Агент удален.")
            except Exception as e:
                pass

    elif action == "delcentr":
        adminData = administration.getAdminById(str(callback.from_user.id))
        if not adminData.superuser:
            await callback.message.reply('У вас недостаточно прав')
            return
        await bot.send_message(chat_id=int(adminData.userId), text="Отправьте токен бота, который является ботом тех-поддержки для канала")
        await state.set_state(MenuState.del_centr)
        await state.update_data(channel_id=channelId)

        @dp.message(MenuState.del_centr)
        async def del_centr(token: types.Message, state: FSMContext):
            chat_data = await state.get_data()
            channel_id = chat_data.get("channel_id")
            try:
                with grpc.insecure_channel('146.0.78.143:5001') as channel:
                    stub = ticket_bot_pb2_grpc.TicketsStub(channel=channel)
                    request = ticket_bot_pb2.ChannelId(channelId=channel_id)
                    callCenter: ticket_bot_pb2.Empty = stub.RemoveCallCenter(
                        request)
            except Exception as e:
                pass

            try:
                with grpc.insecure_channel('146.0.78.143:40001') as channel:
                    stub = bot_manager_pb2_grpc.BotManagerStub(channel=channel)
                    request = bot_manager_pb2.DeleteBotRequest(
                        bot_token=token.text)
                    stub.DeleteBot(request)
            except Exception as e:
                pass

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="Добавить колл-центр", callback_data="cmd_addcentr_" + channel_id)],
                [types.InlineKeyboardButton(
                    text="Назад", callback_data="cmd_back_" + channel_id)]
            ])
            await state.set_state(MenuState.menu)
            await callback.message.edit_text("Колл-центр удален:")
            await callback.message.edit_reply_markup(reply_markup=keyboard)

    elif action == "addcentr":
        adminData = administration.getAdminById(str(callback.from_user.id))
        if not adminData.superuser:
            await callback.message.reply('У вас недостаточно прав')
            return
        await bot.send_message(chat_id=int(adminData.userId), text="Отправьте токен бота, которого вы бы хотели назначить ботом тех-поддержки для канала")
        await state.set_state(MenuState.add_centr)
        await state.update_data(channel_id=channelId)

        @dp.message(MenuState.add_centr)
        async def add_centr(token: types.Message, state: FSMContext):
            chat_data = await state.get_data()
            channel_id = chat_data.get("channel_id")
            try:
                with grpc.insecure_channel('146.0.78.143:5001') as channel:
                    stub = ticket_bot_pb2_grpc.TicketsStub(channel=channel)
                    request = ticket_bot_pb2.RegisterCallcenterRequest(
                        channelId=channel_id)
                    callCenter: ticket_bot_pb2.CallcenterData = stub.RegisterCallcenter(
                        request)
            except Exception as e:
                pass

            try:
                with grpc.insecure_channel('146.0.78.143:40001') as channel:
                    stub = bot_manager_pb2_grpc.BotManagerStub(channel=channel)
                    request = bot_manager_pb2.CreateBotRequest(
                        bot_token=token.text, bot_callcenter=callCenter.externalId, bot_channel_id=channel_id)
                    stub.CreateBot(request)
            except Exception as e:
                pass

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="Настроить колл-центр", callback_data="cmd_setcentr_" + channel_id)],
                [types.InlineKeyboardButton(
                    text="Удалить колл-центр", callback_data="cmd_delcentr_" + channel_id)],
                [types.InlineKeyboardButton(
                    text="Назад", callback_data="cmd_back_" + channelId)]
            ])
            await state.set_state(MenuState.menu)
            await callback.message.edit_text("Колл-центр добавлен:")
            await callback.message.edit_reply_markup(reply_markup=keyboard)

    elif action == "back":
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="Общая статистика", callback_data="cmd_all_" + channelId)],
            [types.InlineKeyboardButton(
                text="Детальная статистика", callback_data="cmd_det_" + channelId)],
            [types.InlineKeyboardButton(
                text="Действия", callback_data="cmd_act_" + channelId)],
            [types.InlineKeyboardButton(
                text="Выход", callback_data="cmd_10_" + channelId)]
        ])
        await callback.message.edit_text("Выберите желаемую информацию об этом канале.")
        await callback.message.edit_reply_markup(reply_markup=keyboard)

    elif action == "10":
        await callback.message.edit_text(f"Завершено")
    await callback.answer()


@dp.callback_query(Text(text_startswith="poll_gender"))
async def add_gender_data(callback: types.CallbackQuery):
    data = callback.data.split("_")
    gender = data[len(data) - 1]
    with grpc.insecure_channel('146.0.78.143:5001') as channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
        request = sub_unsub_pb2.GenderRequest(userId=str(
            callback.from_user.id), gender=gender, channelId=str(callback.message.chat.id))
        messages: sub_unsub_pb2.EmptyMessage = stub.WriteGenderStats(request)
    await callback.answer(text="Ваши данные сохранены")


@dp.callback_query(Text(text_startswith="poll_age"))
async def add_gender_data(callback: types.CallbackQuery):
    data = callback.data.split("_")
    age = data[len(data) - 1]

    with grpc.insecure_channel('146.0.78.143:5001') as channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
        request = sub_unsub_pb2.AgeRequest(userId=str(callback.from_user.id), age=int(
            age), channelId=str(callback.message.chat.id))
        messages: sub_unsub_pb2.EmptyMessage = stub.WriteAgeStats(request)
    await callback.answer(text="Ваши данные сохранены")


@dp.channel_post()
def add_message_to_db(message: types.Message):
    if message.chat.type != 'channel':
        return

    message_id = str(message.message_id)
    channel_id = str(message.chat.id)
    with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(grpc_channel)
        request = sub_unsub_pb2.SaveMessageRequest(
            channelId=channel_id,
            messageId=message_id
        )

        stub.SaveMessage(request)


async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(subscription_loop.main(bot=bot))
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
