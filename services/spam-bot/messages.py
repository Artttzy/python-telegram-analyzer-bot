import grpc
import sub_unsub_pb2
import sub_unsub_pb2_grpc
from settings import CHANNEL_ID


def get_join_messages():
    with grpc.insecure_channel('146.0.78.143:5001') as channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel=channel)
        request = sub_unsub_pb2.AdminChannelId(
            channelId=str(CHANNEL_ID)
        )

        return stub.GetJoinMessage(request)


def get_leave_messages():
    with grpc.insecure_channel('146.0.78.143:5001') as channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel=channel)
        request = sub_unsub_pb2.AdminChannelId(
            channelId=str(CHANNEL_ID)
        )

        return stub.GetLeftMessage(request)


def set_join_messages(messages):
    with grpc.insecure_channel('146.0.78.143:5001') as channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel=channel)
        request = sub_unsub_pb2.SetAnnounceMessagesRequest(
            adminChannel=str(CHANNEL_ID),
            messages=messages
        )

        stub.SetJoinMessageId(request)


def set_leave_messages(messages):
    with grpc.insecure_channel('146.0.78.143:5001') as channel:
        stub = sub_unsub_pb2_grpc.SubscribtionServiceStub(channel=channel)
        request = sub_unsub_pb2.SetAnnounceMessagesRequest(
            adminChannel=str(CHANNEL_ID),
            messages=messages
        )

        stub.SetLeftMessageId(request)
