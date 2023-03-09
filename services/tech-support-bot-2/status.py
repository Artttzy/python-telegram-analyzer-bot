from enum import Enum


class BotState(Enum):
    MENU = 1
    TICKET_OPEN_USER = 2
    TICKET_OPEN_AGENT = 3


class TicketInfo:
    ticket_id: str


class Status:
    current_state = BotState()
    ticket_info: TicketInfo
