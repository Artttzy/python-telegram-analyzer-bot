import sub_unsub_pb2
from datetime import datetime, timezone
import pytz


def message_ids_in_range(messages: sub_unsub_pb2.ChannelMessageList, start: datetime, end: datetime):
    zone = pytz.timezone('Asia/Almaty')
    for msg in messages.messages:
        msg_time = msg.messageDate.ToDatetime(tzinfo=zone)

        if msg_time >= start and msg_time <= end:
            yield int(msg.messageId)
