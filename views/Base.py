from django.http import HttpRequest, HttpResponse
from CTUtil.Response.response import resp_error_json, resp_to_json
from typing import Dict, Union, Type, Any, List
from django.conf.urls import url
from enum import Enum, auto


class RequestCtrlMethods(Enum):
    delete = auto()
    add = auto()
    update = auto()
    query = auto()

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()


class BaseViewMeta(type):
    def __new__(cls, clsname, bases, clsdict: Dict[str, Any]):
        must_argv: List[str] = ['model_name', 'route_name']
        for argv in must_argv:
            if bases and not clsdict.setdefault(argv, None):
                raise ValueError('Views must be model_name and route_name')
        return super().__new__(cls, clsname, bases, clsdict)


class BaseView(object):

    model_name = None
    route_name = None
    process_request = []

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def process_request_post(
            self, request: HttpRequest) -> Dict[str, Union[str, int]]:
        data = request.POST.copy()
        _data: Dict[str, str] = {}
        for key in data:
            _data[key] = data.setdefault(key, '')
        return _data

    def query(self, request: HttpRequest) -> HttpResponse:
        return_data = {
            'state': 0,
            'data': list(self.model_name.objects.all()),
        }
        return resp_to_json(return_data)

    def delete(self, request: HttpRequest) -> HttpResponse:
        reqall: Dict[str, str] = request.POST
        _id: int = int(reqall.get('id', 0))
        if not _id:
            return resp_error_json('id不允许为空')
        query = self.model_name.objects.filter(id=_id)
        if not query:
            return resp_error_json('数据不存在')
        query.delete()
        return_data: Dict[str, Union[str, int]] = {
            'state': 0,
            'data': '删除成功',
        }
        return resp_to_json(return_data)

    def update(self, request: HttpRequest) -> HttpResponse:
        reqall: Dict[str, str] = self.process_request_post(request)
        _id: int = int(reqall.setdefault('id', 0))
        if not _id:
            return resp_error_json('id不允许为空')
        reqall.pop('id')
        query = self.model_name.objects.filter(id=_id)
        if not query:
            return resp_error_json('数据不存在')
        query.update(**reqall)
        return_data: Dict[str, Union[str, int]] = {
            'state': 0,
            'data': '修改成功',
        }
        return resp_to_json(return_data)

    def add(self, request: HttpRequest) -> HttpResponse:
        reqall: Dict[str, Union[str, int]] = self.process_request_post(request)
        if 'id' in reqall:
            del reqall['id']
        self.model_name.objects.create(**reqall)
        return_data: Dict[str, Union[str, int]] = {
            'state': 0,
            'data': '新增成功',
        }
        return resp_to_json(return_data)

    @classmethod
    def as_view(cls, _method: Type[RequestCtrlMethods], **init):
        def view(request: HttpRequest, *args, **kwargs):
            self = cls(**init)
            return self.dispatch(_method, request, *args, **kwargs)
        return view

    def dispatch(self, _method: Type[RequestCtrlMethods], request, *args, **kwargs):
        handle = getattr(self, _method.name)
        for func in self.process_request:
            handle = func(handle)
        return handle(request, *args, **kwargs)

    @classmethod
    def as_urls(cls, django_url_list):
        for control_method in RequestCtrlMethods:
            path = '{method_name}-{route_name}'.format(
                method_name=control_method,
                route_name=cls.route_name, )
            django_url_list.append(url(path, cls.as_view(control_method)))
