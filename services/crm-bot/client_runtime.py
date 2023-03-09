from pyrogram import Client
from pyrogram.handlers import MessageHandler
from pyrogram import filters
import handlers

sessions = dict()


async def run(account: Client):
    account.add_handler(MessageHandler(
        handlers.message_from_user, filters.incoming))
    await account.start()
    me = await account.get_me()
    sessions[me.id] = account


async def send_message(from_id: int, to_id: str, message: str):
    client: Client = sessions[from_id]
    await client.send_message(chat_id=to_id, text=message)
