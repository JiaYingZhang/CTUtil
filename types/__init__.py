from enum import Enum, auto


class ResponseStatus(Enum):
    SUCCESS = 0
    NOMAL_ERROR = auto()
    LOGIN_ERROR = auto()


class IsOrNot(Enum):
    NOT = 0
    IS = 1
