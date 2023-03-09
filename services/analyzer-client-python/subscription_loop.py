import asyncio
from aiogram import Bot
import grpc
import sub_unsub_pb2_grpc
import sub_unsub_pb2

def get_admin_channels(stub: sub_unsub_pb2_grpc.SubscribtionServiceStub):
    request = sub_unsub_pb2.EmptyMessage()
    response: sub_unsub_pb2.AdminChannelList = stub.GetAdminChannels(request)
    return response.channels


async def get_channel_subsctiption_count(bot: Bot, channel: sub_unsub_pb2.AdminChannel) -> int:
    print(channel.channelId)
    sub_count = await bot.get_chat_members_count(channel.channelId)
    return sub_count
    

def push_channel_data(stub: sub_unsub_pb2_grpc.SubscribtionServiceStub, stat):
    channel: sub_unsub_pb2.AdminChannel = stat[0]
    request = sub_unsub_pb2.PushSubscriberHistoryMessage(channelId=channel.channelId, value=stat[1])
    stub.PushSubscriberHistory(request)


async def channel_check_loop(bot: Bot):
    with grpc.insecure_channel('146.0.78.143:5001') as grpc_channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(grpc_channel)
        channels = get_admin_channels(stub=stub)
        channel_stats: list = []

        for channel in channels:
            try:
                sub_count = await get_channel_subsctiption_count(bot, channel)
                channel_stats.append((channel, sub_count))
            except Exception as e:
                pass

        for stat in channel_stats:
            push_channel_data(stub=stub, stat=stat)


async def main(bot: Bot):
    while True:
        try:
            await channel_check_loop(bot=bot)
        except Exception:
            pass

        # Проверка каждый час (Бэкенд будет записывать максимальное значение за день)
        await asyncio.sleep(3600)
