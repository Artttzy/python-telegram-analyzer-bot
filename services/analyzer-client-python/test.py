import asyncio
from telethon import TelegramClient
from telethon.sessions import SQLiteSession

user_client = TelegramClient(
    "rtz",
    api_id=21589305,
    api_hash="b6e091c1a7dc9de7b031fd55bd3855b6"
)

async def send_msge(text):
    await user_client.connect()
    await user_client.send_message("antttezy", text)

if __name__ == "__main__":
    asyncio.run(send_msge("SUPCHIK"))