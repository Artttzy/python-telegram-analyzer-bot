from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,\
    InlineKeyboardMarkup, InlineKeyboardButton


def create_goto_user_keyboard_username(ticket_id, username):
    keyboard = [
        [InlineKeyboardButton(text='Перейти в ЛС',
                              url=f'http://t.me/{username}')],
        [InlineKeyboardButton(text='Я ответил',
                              callback_data=f'loganswer_{ticket_id}')]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_close_button(ticket_id):
    return InlineKeyboardButton(text='Вопрос решен',
                                callback_data=f'close_ticket_{ticket_id}')


def create_workday_keyboard():
    keyboard = [
        [KeyboardButton(text='Рабочий день')]
    ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def set_workday_keyboard(text, set_enabled):
    callback_payload = None

    if set_enabled:
        callback_payload = '1'
    else:
        callback_payload = '0'

    keyboard = [
        [InlineKeyboardButton(text=text,
                              callback_data=f'set_work_enabled_{callback_payload}'
                              )]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
