from aiogram import F, Router, Bot
from aiogram.dispatcher.filters.chat_member_updated import \
    ChatMemberUpdatedFilter, KICKED, LEFT, \
    RESTRICTED, MEMBER, ADMINISTRATOR, CREATOR
from aiogram.types import ChatMemberUpdated
import grpc
import sub_unsub_pb2_grpc
import sub_unsub_pb2
from google.protobuf import timestamp_pb2
from datetime import datetime, timezone

router = Router()


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=(KICKED | LEFT | RESTRICTED)
                                            <<
                                            (ADMINISTRATOR | CREATOR | MEMBER)))
async def on_user_leave(event: ChatMemberUpdated):
    with grpc.insecure_channel('146.0.78.143:5001') as channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(datetime.now(tz=timezone.utc))
        request = sub_unsub_pb2.SubUnsubEvent(
            id=str(event.new_chat_member.user.id),
            channelId=str(event.chat.id),
            time=timestamp,
            subStatus='left'
        )

        response = sub_unsub_pb2.EventResponse()
        stub.TriggerEvent(request)
