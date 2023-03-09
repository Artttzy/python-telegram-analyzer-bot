from pyrogram import Client
from pyrogram.types import Message
from session_storage import handle_message


async def message_from_user(client: Client, message: Message):
    self_id = (await client.get_me()).id
    sender = message.from_user
    text = message.text

    if sender.username is not None:
        await handle_message(self_id=self_id, chat_id=sender.username, text=text)
