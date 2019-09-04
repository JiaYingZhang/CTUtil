from typing import Callable, Any, Optional, Tuple, Dict, Type
from CTUtil.util import jstimestamp_to_datetime
from django.db import models

__all__ = ['Field', 'CharField', 'IntField', 'JsTimeStampField', 'Form']


class Field(object):

    def __init__(
            self,
            backend: str,
            valid_func: Optional[Callable[[Any], Tuple[Any, str]]] = None):
        self.backend = backend
        self.valid_func = valid_func

    def valid(self, value: Any) -> Tuple[Any, str]:
        if self.valid_func:
            return self.valid_func(value)
        return value, ''


class CharField(Field):

    def valid(self, value):
        value, err = super().valid(str(value))
        if err != '':
            return value, err
        return value, err


class IntField(Field):

    def valid(self, value):
        value, err = super().valid(int(value))
        if err != '':
            return value, err
        return value, err


class JsTimeStampField(Field):

    def valid(self, value):
        value, err = super().valid(value)
        if err != '':
            return value, err
        return jstimestamp_to_datetime(int(value)), err


class ModelField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model: Type[model] = kwargs.setdefualt('model', None)

    def valid(self, value):
        if not self.model:
            raise ValueError('ModelField must be model arg')
        value, err = super().valid(value)
        if err != '':
            return value, err
        return self.model.objects.get(pk=value)


class FormMeta(type):

    def __new__(cls, clsname: str, bases: Tuple[object],
                clsdict: Dict[str, Any]):
        fields: Dict[str, Field] = {}
        for key, filed in clsdict.items():
            if isinstance(filed, Field):
                fields[key] = filed
        for key in fields.keys():
            del clsdict[key]
        clsdict['fields'] = fields
        return super().__new__(cls, clsname, bases, clsdict)


class Form(metaclass=FormMeta):

    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.error: Dict[str, str] = {}
        self.backend: Dict[str, Any] = {}

    def is_valid(self) -> bool:
        self.error.clear()
        self.backend.clear()
        self.fields: dict
        isvalid: bool = True
        for name, value in self.data.items():
            field: Type[Field] = self.fields.setdefault(name)
            if not field:
                continue
            value, err = field.valid(value)
            if err != '':
                self.error[name] = err
                isvalid = False
            else:
                self.backend[field.backend] = value
        return isvalid
