from django.http import HttpResponse, HttpRequest
from django.utils.deprecation import MiddlewareMixin
from typing import Optional, Union, NewType, NamedTuple, Any
import redis
import pickle
import hashlib
from functools import wraps
from CTUtil.types import HTTPResponseStates
from typing import NamedTuple
import time
import json
from datetime import datetime

MD5Str = NewType('MD5Str', str)
expire: int = 60 * 60 * 24


class RedisObject(NamedTuple):
    expire: Optional[float]
    value: Any

    @property
    def is_expire(self):
        if self.expire:
            return time.time() > self.expire
        else:
            return False

    def __str__(self):
        return json.dumps(
            {
                'expire': datetime.fromtimestamp(self.expire).isoformat(),
                'is_expire': self.is_expire,
            },
            ensure_ascii=False)


RedisPool: redis.ConnectionPool = redis.ConnectionPool()

_using: redis.Redis = redis.Redis(connection_pool=RedisPool)
_table: str = 'default'


class Cache:

    def __init__(self,
                 using: Optional[redis.Redis] = None,
                 table: Optional[str] = _table,
                 is_never_expire=False):
        self.using = _using if not using else using
        self.table: Optional[str] = table
        self.is_never_expire: bool = is_never_expire

    def add(self, key: str, value: Any, expire: Optional[int] = None):
        key = self.get_md5_key(key)
        if not expire:
            if self.is_never_expire:
                expire_time: Union[float, None] = None
            else:
                expire_time = time.time() + 60 * 60 * 24
        else:
            expire_time = time.time() + expire
        o: RedisObject = RedisObject(expire=expire_time, value=value)
        v: bytes = pickle.dumps(o)
        self.using.hset(self.table, key, v)

    def delete(self, key: str):
        key = self.get_md5_key(key)
        self.using.hdel(self.table, key)

    def update(self, key: str, value: Any, expire: Optional[int] = None):
        return self.add(key, value, expire)

    def clear(self):
        self.using.delete(self.table)

    def get(self, key: str) -> Any:
        key = self.get_md5_key(key)
        v: bytes = self.using.hget(self.table, key)
        if not v:
            return None
        o: RedisObject = pickle.loads(v)
        if o.is_expire:
            self.using.hdel(self.table, key)
            return None
        else:
            return o.value

    def __len__(self) -> int:
        if getattr(self, '_length', None) is None:
            self._length: int = self.using.hlen(self.table)
        return self._length

    @classmethod
    def get_md5_key(cls, key: str) -> MD5Str:
        return MD5Str(hashlib.md5(key.encode()).hexdigest())


class DjangoHttpMixin:

    @classmethod
    def make_request_key(cls, request: HttpRequest) -> str:
        base: str = request.path + json.dumps(request.POST.copy())
        try:
            d: str = json.dumps(json.loads(request.body), ensure_ascii=False)
            return base + d
        except:
            return base

    @classmethod
    def cache_response(cls,
                       cache: Optional[Cache] = None,
                       expire: Optional[int] = None):

        def _cached_response(func):

            @wraps(func)
            def _set_caches(*args, **kwargs):
                request: HttpRequest = args[-1]
                resp: HttpResponse = func(*args, **kwargs)
                try:
                    if resp.status_code == HTTPResponseStates.SUCCESS:
                        c = cache if cache is not None else Cache()
                        key: str = cls.make_request_key(request)
                        c.add(key, pickle.dumps(resp), expire=expire)
                except:
                    pass
                return resp

            return _set_caches

        return _cached_response