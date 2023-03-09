from pyrogram import Client
import json
from pyrogram.raw.functions.contacts import ResolveUsername
from pyrogram.raw.functions.stats import GetBroadcastStats
from pyrogram.raw.base import StatsAbsValueAndPrev
from pyrogram.raw.types.stats import BroadcastStats
from pyrogram.raw.functions.messages import GetMessagesViews
from pyrogram.raw.types.messages import MessageViews
from pyrogram.types import Message
from pyrogram.raw.base import InputChannel
from pyrogram import types, filters, enums

pyrogram_client = Client(
    "bot",
    api_id=21589305,
    api_hash="b6e091c1a7dc9de7b031fd55bd3855b6",
    bot_token="5769910363:AAEvWdHotYX2stcYj44J4RlX7Xhocim99FQ",
)

user_client = Client(
    "my_account",
    api_id=21589305,
    api_hash="b6e091c1a7dc9de7b031fd55bd3855b6"
)


async def resolve_username_to_user_id(username: str):
    if not pyrogram_client.is_connected:
        await pyrogram_client.start()
    with pyrogram_client:
        r = await pyrogram_client.invoke(ResolveUsername(username=username))
        if r.users:
            return r.users[0].id
        return None

async def get_username_by_user_id(id: int):
    if not pyrogram_client.is_connected:
        await pyrogram_client.start()
    with pyrogram_client:
        r = await pyrogram_client.get_users(id)
        if r.username:
            return r.username
        return None

async def get_message_views(channelId, messageids):
    if (len(messageids) == 0):
        return [0, 0]
    if not pyrogram_client.is_connected:
        await pyrogram_client.start()
    with pyrogram_client:
        count : float = 0
        messages  = await pyrogram_client.get_messages(chat_id=int(channelId), message_ids=messageids)
        for message in messages:
            if (message.views == None):
                continue
            count += message.views
        avg = count / len(messageids)
        return [avg, count]

async def get_message_reactions(channelId, messageids):
    if (len(messageids) == 0):
        return 0
    if not pyrogram_client.is_connected:
        await pyrogram_client.start()
    with pyrogram_client:
        count : float = 0
        messages  = await pyrogram_client.get_messages(chat_id=int(channelId), message_ids=messageids)
        for message in messages:
            reactions = message.reactions
            if (reactions == None):
                continue
            for reaction in reactions:
                count += reaction.count
        ans = count / len(messageids)
        return ans

        
async def get_message_reactions_by_user(channelId, messageids):
    if (len(messageids) == 0):
        return [0, 0]
    if not user_client.is_connected:
        await user_client.start()
    with user_client:
        count : float = 0
        messages  = await user_client.get_messages(chat_id=int(channelId), message_ids=messageids)
        for message in messages:
            if (message.reactions == None):
                continue
            reactions = message.reactions.reactions
            for reaction in reactions:
                count += reaction.count
        ans = count / len(messageids)
        return [ans, count]


async def get_chat_members(channelId):
    if not pyrogram_client.is_connected:
        await pyrogram_client.start()

    with pyrogram_client:
        members = user_client.get_chat_members()
        return members
