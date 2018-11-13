from enum import Enum, auto
from json import JSONEncoder
from typing import Type


class EnumJsonEncode(JSONEncoder):
    def default(self, obj: Type[Enum]):
        if isinstance(obj, Enum):
            return obj.value
        return JSONEncoder.default(self, obj)


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


class EmailTypes(Enum):
    DEMAND = auto()
    BUG = auto()
    ZHAOPING = auto()