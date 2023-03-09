from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,\
    InlineKeyboardMarkup, InlineKeyboardButton


def create_menu_keyboard():
    keyboard = [
        [KeyboardButton(text='Открыть тикет 🎫')]
    ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def create_close_ticket_button(ticket_id):
    keyboard = [
        [InlineKeyboardButton(text='Закрыть тикет',
                              callback_data=f'close_ticket_{ticket_id}')]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_open_ticket_button():
    keyboard = [
        [InlineKeyboardButton(text='Открыть тикет',
                              callback_data='open_ticket')]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
