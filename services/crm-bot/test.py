from telethon import TelegramClient

client = TelegramClient('6283153275787', api_id=8,
                        api_hash='7245de8e747a0d6fbe11f7cc14fcc0bb')


async def main():
    me = await client.get_me()
    print(me)


with client:
    client.loop.run_until_complete(main())
