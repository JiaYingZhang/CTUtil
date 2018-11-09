from typing import Dict, Any, Any
from copy import deepcopy


class FrontFiledParse(object):
    raw = []
    to = []

    def __init__(self, data: Dict[Any, Any]):
        self.raw_data = data
        self._data = {}

    @property
    def data(self):
        if self._data:
            return self._data
        data = deepcopy(self.raw_data)
        for _, i in enumerate(self.raw):
            if i in data:
                self._data.setdefault(self.to[_], data[i])
                self._data.pop(i)
        self._data = data
        return self._data
