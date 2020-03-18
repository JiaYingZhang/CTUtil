from django.http import HttpRequest, HttpResponse
from CTUtil.response import resp_error_json, resp_to_json
from typing import Dict, Union, Any, List, Optional
from functools import wraps
from django.conf.urls import url
import inspect
from CTUtil.util import set_default_file_path


def exclude(func):
    @wraps(func)
    def _exclude(*args, **kwargs):
        return func(*args, **kwargs)
    setattr(_exclude, 'view', False)
    return _exclude


class BaseViewMeta(type):
    def __new__(cls, clsname, bases, clsdict: Dict[str, Any]):
        router_key = ['route_name', 'router_name', 'router']
        model_key = ['model_name', 'model']

        for k in router_key:
            router = clsdict.get(k, None)
            if router:
                break
        for k in model_key:
            model = clsdict.get(k, None)
            if model:
                break

        if clsdict.setdefault('abstract', False) is False:
            if bases and not all([model, router]):
                raise ValueError('Views must be model and router')
        clsdict['model'] = model
        clsdict['router'] = f'{router}/' if router and not router.endswith('/') else router
        return super().__new__(cls, clsname, bases, clsdict)


class BaseView(metaclass=BaseViewMeta):

    model_name = None
    route_name = None
    abstract = True
    process_request = []
    page_key = 'pageNo'
    size_key = 'pageSize'
    page_max_size = 40
    pk_key = 'id'

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def reqall(self) -> dict:
        if getattr(self, '_reqall', None) is None:
            self._reqall = self.process_request_post(self.request)
        return self._reqall

    @property
    def ins(self):
        if getattr(self, '_ins', False) is False:
            pk = self.reqall.setdefault(self.pk_key)
            if not pk:
                self._ins = None
            else:
                self._ins = self.model.objects.filter(pk=pk).first()
        return self._ins


    @property
    def page(self):
        if getattr(self, '_page', None) is None:
            page: Union[str, int] = self.reqall.get(self.page_key, 1)
            if isinstance(page, str):
                if page.isdigit():
                    self._page = int(page)
                else:
                    self._page = 1
            elif isinstance(page, int):
                self._page = page
            else:
                self._page = 1
        return self._page

    @property
    def size(self):
        if getattr(self, '_size', None) is None:
            size: Union[str, int] = self.reqall.get(self.size_key, self.page_max_size)
            if isinstance(size, str):
                if size.isdigit():
                    self._size = int(size)
                else:
                    self._size = self.page_max_size
            elif isinstance(size, int):
                self._size = size
            else:
                self._size = self.page_max_size
            if self._size > self.page_max_size:
                self._size = self.page_max_size
        return self._size

    @exclude
    def process_request_post(
            self, request: HttpRequest) -> Dict[str, Union[str, int]]:
        data = request.POST.copy()
        _data: Dict[str, str] = {}
        for key in data:
            _data[key] = data.setdefault(key, '')
        files = request.FILES.copy()
        for name, f in files.items():
            file_type = (f.name).split('.')[-1]
            file_path = set_default_file_path(file_type=file_type)
            if not file_path:
                continue
            with open(file_path, 'wb+') as f:
                for chunk in f.chunks():
                    f.write(chunk)
            _data[name] = file_path
        return _data

    def query(self, request: HttpRequest) -> HttpResponse:
        return_data = {
            'state': 0,
            'data': list(self.model.objects.all()),
        }
        return resp_to_json(return_data)

    def delete(self, request: HttpRequest) -> HttpResponse:
        reqall: Dict[str, str] = self.process_request_post(request)
        _id: int = int(reqall.get('id', 0))
        if not _id:
            return resp_error_json('id不允许为空')
        query = self.model.objects.filter(id=_id)
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
        obj = self.model.objects.filter(id=_id).first()
        if not obj:
            return resp_error_json('数据不存在')
        for key, value in reqall.items():
            setattr(obj, key, value)
        obj.save()
        return_data: Dict[str, Union[str, int]] = {
            'state': 0,
            'data': '修改成功',
        }
        return resp_to_json(return_data)

    def add(self, request: HttpRequest) -> HttpResponse:
        reqall: Dict[str, Union[str, int]] = self.process_request_post(request)
        if 'id' in reqall:
            del reqall['id']
        self.model.objects.create(**reqall)
        return_data: Dict[str, Union[str, int]] = {
            'state': 0,
            'data': '新增成功',
        }
        return resp_to_json(return_data)

    @classmethod
    def as_views(cls, method_name: str, **init):
        def view(reqeust: HttpRequest, *args, **kwargs):
            init['request'] = reqeust
            self = cls(**init)
            return self.dispatch(method_name, reqeust, *args, **kwargs)
        return view

    def dispatch(self, method_name: str, request, *args, **kwargs):
        handle = getattr(self, method_name)
        for func in self.process_request:
            handle = func(handle)
        return handle(request, *args, **kwargs)

    @classmethod
    def as_urls(cls, django_url_list):
        for k, v in cls.__dict__.items():
            k: str
            if k.startswith('_', ):
                continue
            if inspect.isfunction(v):
                if not getattr(v, 'view', True):
                    continue
                sig: inspect.Signature = inspect.signature(v)
                if str(sig.return_annotation) == str(HttpResponse) or sig.return_annotation == sig.empty:
                    name: str = k.replace('_', '-')
                    path = f'{name}-{cls.router}'
                    django_url_list.append(url(path, cls.as_views(k)))
