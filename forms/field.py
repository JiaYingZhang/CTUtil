from typing import Callable, Any, Optional, Tuple, Dict, Type, Union
from CTUtil.util import jstimestamp_to_datetime
from django.db import models
from copy import deepcopy

__all__ = ['Field', 'CharField', 'IntField', 'JsTimeStampField', 'Form']
"""
前端数据:
data = {
    'front_key': 'value'
}
form = Form(data)
form.backend => 转换成后端数据

backend_data = {
    'backend_key': 'value'
}
Form.to_forn(backend_data) => data

"""


class Field(object):

    def __init__(self,
                 backend: str = None,
                 ignore: bool = False,
                 valid_func: Optional[Callable[[Any], Tuple[Any, str]]] = None,
                 display: Optional[Callable[[Any], Any]] = None):
        self.backend = backend
        self._valid_func = valid_func
        self.ignore = ignore
        self._display = display

    def valid(self, value: Any) -> Tuple[Any, str]:
        if self._valid_func:
            return self._valid_func(value)
        return value, ''


class CharField(Field):

    def valid(self, value):
        value, err = super().valid(str(value))
        if err != '':
            return value, err
        return value, err


class IntField(Field):

    def valid(self, value):
        value, err = super().valid(value)
        if err != '':
            return value, err
        if not value:
            return value, err
        return int(value), err


class JsTimeStampField(Field):

    def valid(self, value):
        value, err = super().valid(value)
        if err != '':
            return value, err
        if not value:
            return value, err
        return jstimestamp_to_datetime(int(value)), err


class ModelField(Field):

    def __init__(self, *args, **kwargs):
        kwargs: dict
        self.model: Type[model] = kwargs.pop('model', None)
        super().__init__(*args, **kwargs)

    def valid(self, value):
        if not self.model:
            raise ValueError('ModelField must be model arg')
        value, err = super().valid(value)
        if err != '':
            return value, err
        try:
            ins = self.model.objects.get(pk=value)
        except:
            ins = None
        return ins, err


class FormMeta(type):

    def __new__(cls, clsname: str, bases: Tuple[type],
                clsdict: Dict[str, Any]):
        fields: Dict[str, Field] = {}
        for base in bases:
            _fields = getattr(base, 'fields', {})
            if _fields:
                for key, value in _fields.items():
                    if key in clsdict:
                        continue
                    clsdict[key] = value
        for key, filed in clsdict.items():
            if isinstance(filed, Field):
                fields[key] = filed
        for key in fields.keys():
            if key in clsdict:
                del clsdict[key]
        clsdict['fields'] = fields

        return super().__new__(cls, clsname, bases, clsdict)


class Form(metaclass=FormMeta):

    def __init__(self,
                 data: Union[Dict[str, Any], Type[models.Model]],
                 model: Optional[Type[models.Model]] = None):
        self.data = data
        self.model = model
        self.error: Dict[str, str] = {}
        self.backend: Dict[str, Any] = {}

    def is_valid(self) -> bool:
        self.error.clear()
        self.backend.clear()
        self.fields: dict
        isvalid: bool = True

        if not isinstance(self.data, dict):
            self.data = self.data.__dict__
        for name, value in self.data.items():
            field: Field = self.fields.get(name, None)
            if not field or field.ignore:
                continue
            value, err = field.valid(value)
            if err != '':
                self.error[name] = err
                isvalid = False
            else:
                self.backend[field.backend] = value
        return isvalid

    @property
    def front(self) -> dict:
        if getattr(self, '_front', None) is None:
            self._front: dict = {}

            _getattr = (lambda : self.data.get \
                if isinstance(self.data, dict) else lambda name, default: getattr(self.data, name, default)) ()
            for front, field in self.fields.items():
                try:
                    value = _getattr(field.backend, None)
                except:
                    value = None
                if field._display:
                    self._front[front] = field._display(value)
                else:
                    self._front[front] = value
        return self._front

    def create_or_update(self,
                         expand_data: Optional[dict] = None,
                         pk_key='id',
                         raise_error: bool = False):
        if not self.model:
            raise TypeError('must model')
        if self.is_valid():
            data = deepcopy(self.backend)
            if expand_data:
                data.update(expand_data)
            pk: str = data.pop(pk_key, '')
            if not pk:
                ins = self.model.objects.create(**data)
                return ins
            else:
                ins = self.model.objects.filter(**{pk_key: pk}).first()
                if not ins:
                    return None
                for key, value in data.items():
                    setattr(ins, key, value)
                ins.save()
                return ins
        if raise_error:
            raise ValueError(self.error)
