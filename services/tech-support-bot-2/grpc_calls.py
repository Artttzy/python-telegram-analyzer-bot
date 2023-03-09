import ticket_bot_pb2_grpc
from grpc import insecure_channel
from ticket_bot_pb2 import OpenTicketRequest, TicketData, SupportStatus,\
    GetStatusRequest, CloseTicketRequest, TicketIdRequest,\
    CheckAvailableAgentsRequest, UserMessageRequest,\
    WorkdayData
from settings import CHANNEL_ID, CHANNEL_LINK, CALL_CENTER_ID


def create_grpc_link():
    return insecure_channel(CHANNEL_LINK)


def open_ticket(user_id) -> TicketData:
    with create_grpc_link() as grpc_channel:
        stub = ticket_bot_pb2_grpc.TicketsStub(grpc_channel)
        request = OpenTicketRequest(
            userId=str(user_id),
            callCenterId=CALL_CENTER_ID,
            channelId=CHANNEL_ID
        )

        response: TicketData = stub.OpenTicket(request=request)
        return response


def get_status(user_id) -> SupportStatus:
    with create_grpc_link() as grpc_channel:
        stub = ticket_bot_pb2_grpc.TicketsStub(grpc_channel)
        request = GetStatusRequest(
            userId=str(user_id),
            callcenterId=CALL_CENTER_ID
        )

        return stub.GetStatus(request)


def close_ticket(ticket_id):
    with create_grpc_link() as grpc_channel:
        stub = ticket_bot_pb2_grpc.TicketsStub(grpc_channel)
        request = CloseTicketRequest(
            ticketId=int(ticket_id)
        )

        return stub.CloseTicket(request)


def log_agent_message(ticket_id):
    with create_grpc_link() as grpc_channel:
        stub = ticket_bot_pb2_grpc.TicketsStub(grpc_channel)
        request = TicketIdRequest(
            ticketId=int(ticket_id)
        )

        stub.LogAgentMessage(request)


def log_user_message(ticket_id, message_id):
    with create_grpc_link() as grpc_channel:
        stub = ticket_bot_pb2_grpc.TicketsStub(grpc_channel)
        request = UserMessageRequest(
            ticketId=int(ticket_id),
            messageId=str(message_id)
        )

        return stub.LogUserMessage(request)


def check_available_agent(callcenter_id):
    with create_grpc_link() as grpc_channel:
        stub = ticket_bot_pb2_grpc.TicketsStub(grpc_channel)
        request = CheckAvailableAgentsRequest(
            callCenterId=str(callcenter_id)
        )

        return stub.CheckAvailableAgents(request)


def get_workday_status(user_id):
    with create_grpc_link() as grpc_channel:
        stub = ticket_bot_pb2_grpc.TicketsStub(grpc_channel)
        request = GetStatusRequest(
            userId=str(user_id),
            callcenterId=CALL_CENTER_ID
        )

        return stub.GetWorkday(request)

def set_workday_status(user_id, is_working):
    with create_grpc_link() as grpc_channel:
        stub = ticket_bot_pb2_grpc.TicketsStub(grpc_channel)
        request = WorkdayData(
            agentId=str(user_id),
            callCenterId=CALL_CENTER_ID,
            isWorking=is_working
        )

        return stub.SetWorkday(request)