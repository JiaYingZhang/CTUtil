from copy import deepcopy
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union

from django.db import models

from CTUtil.util import jstimestamp_to_datetime

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
                 backend: Optional[str] = None,
                 ignore: bool = False,
                 valid_func: Optional[Callable[[Any], Tuple[Any, str]]] = None,
                 display: Optional[Callable[[Any], Any]] = None,
                 method_name: Optional[str] = None):
        self.backend = backend
        self._valid_func = valid_func
        self.ignore = ignore
        self._display = display or self.display
        self.method_name = method_name

    def valid(self, value: Any) -> Tuple[Any, str]:
        return value, ''

    def display(self, value: Any) -> Any:
        return value


class CharField(Field):

    def valid(self, value):
        if not value:
            return '', ''
        else:
            value, err = super().valid(str(value))
        if err != '':
            return value, err
        return value, err

    def display(self, value: Any) -> Any:
        if not value:
            return ''
        return str(value)


class IntField(Field):

    def valid(self, value):
        value, err = super().valid(value)
        if err != '':
            return value, err
        if not value:
            return value, err
        return int(value), err

    def display(self, value: Any) -> Any:
        return int(value)


class JsTimeStampField(Field):

    def valid(self, value):
        value, err = super().valid(value)
        if err != '':
            return value, err
        if not value:
            return None, err
        return jstimestamp_to_datetime(int(value)), err

    def display(self, value: Any) -> Any:
        return value and format(value, '%Y-%m-%d %H:%M:%s')


class ObjectDateField(Field):

    def valid(self, value: Union[str, dict]):
        if isinstance(value, dict):
            value = self._parse_date(value)
        return value, ''

    def _parse_date(self, obj: dict):
        d = f"{obj.get('year', '')}-{obj.get('month', '')}-{obj.get('day', '')}"

        length = len(d)
        end = length
        for i in range(length - 1, -1, -1):
            char = d[i]
            if char.isdigit():
                return d[:end]
            else:
                end -= 1
        return ''

    def display(self, value: str):
        if not value:
            return ''
        date = value.split('-')
        year, month, day = '', '', ''
        for i in date:
            if not year:
                year = i
            elif not month:
                month = i
            elif not day:
                day = i
        return {
            'year': year,
            'month': month,
            'day': day,
        }


class ModelField(Field):

    def __init__(self, *args, **kwargs):
        self.model: Type[models.Model] = kwargs.pop('model', None)
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

    def __new__(cls, clsname: str, bases: Tuple[type], clsdict: Dict[str,
                                                                     Any]):
        fields: Dict[str, Field] = {}
        field_mapping: Dict[str, Optional[str]] = {}
        for base in bases:
            _fields = getattr(base, 'fields', {})
            if _fields:
                for key, value in _fields.items():
                    if key in clsdict:
                        continue
                    clsdict[key] = value
        for key, field in clsdict.items():
            if isinstance(field, Field):
                fields[key] = field
        for key in fields.keys():
            if key in clsdict:
                del clsdict[key]

        for key, field in fields.items():
            field_mapping[key] = field.backend
        clsdict['fields'] = fields
        clsdict['field_mapping'] = field_mapping

        return super().__new__(cls, clsname, bases, clsdict)


class Form(metaclass=FormMeta):

    field_mapping: Dict[str, Optional[str]]
    fields: Dict[str, Field]

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
        isvalid: bool = True

        if not isinstance(self.data, dict):
            self.data = self.data.__dict__
        for name, value in self.data.items():
            field: Optional[Field] = self.fields.get(name, None)
            if not field or field.ignore:
                continue
            value, err = field.valid(value)
            if field._valid_func:
                value, err = field._valid_func(value)
            if err != '':
                self.error[name] = err
                isvalid = False
            else:
                if field.backend:
                    self.backend[field.backend] = value
        return isvalid

    @property
    def front(self) -> dict:
        if getattr(self, '_front', None) is None:
            self._front: dict = {}

            _getattr = (lambda: self.data.get
                        if isinstance(self.data, dict) else lambda name,
                        default: getattr(self.data, name, default))()
            for front, field in self.fields.items():
                try:
                    value = _getattr(field.backend, None)
                except:
                    value = None
                if field.method_name:
                    method = getattr(self, field.method_name, None)
                    if method is None:
                        raise TypeError(f'Form must {field.method_name} method')
                    self._front[front] = method(value)
                elif field._display:
                    self._front[front] = field._display(value)
                else:
                    self._front[front] = value
        return self._front

    def create_or_update(self,
                         expand_data: Optional[dict] = None,
                         pk_key='id',
                         raise_error: bool = False) -> Any:
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
                    data[pk_key] = pk
                    ins = self.model.objects.create(**data)
                    return ins
                for key, value in data.items():
                    setattr(ins, key, value)
                ins.save()
                return ins
        if raise_error:
            raise ValueError(self.error)
