from enum import Enum, auto, IntEnum
from json import JSONEncoder
from typing import Type


class EnumJsonEncode(JSONEncoder):
    def default(self, obj: Type[Enum]):
        if isinstance(obj, Enum):
            return obj.value
        return JSONEncoder.default(self, obj)


class ResponseStates(IntEnum):
    SUCCESS = 0
    NOMAL_ERROR = auto()
    LOGIN_ERROR = auto()


class IsOrNot(IntEnum):
    NOT = 0
    IS = 1


class HTTPResponseStates(IntEnum):
    SUCCESS = 200
    NOTFOUND = 400
    ERROR = 500
    FORBIDDEN = 403


class EmailTypes(IntEnum):
    DEMAND = auto()
    BUG = auto()
    RECRUIT = auto()


class FuncCallBack(IntEnum):
    FAIL = 0
    SUCCESS = 1
