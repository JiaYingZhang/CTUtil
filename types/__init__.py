from enum import Enum, auto


class ResponseStates(Enum):
    SUCCESS = 0
    NOMAL_ERROR = auto()
    LOGIN_ERROR = auto()


class IsOrNot(Enum):
    NOT = 0
    IS = 1


class HTTPResponseStates(Enum):
    SUCCESS = 200
    NOTFOUND = 400
    ERROR = 500
    FORBIDDEN = 403
