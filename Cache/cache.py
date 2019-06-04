from django.http import HttpResponse, HttpRequest
from django.utils.deprecation import MiddlewareMixin
from typing import Optional, Union, NewType, NamedTuple
import redis
import pickle
import hashlib
from functools import wraps
from CTUtil.types import HTTPResponseStates
from django.conf import settings
from typing import NamedTuple
import time
import json

MD5Str = NewType('MD5Str', str)
expire: int = 60 * 60 * 24

class RedisObject(NamedTuple):
    expire: float
    value: bytes

try:
    config: dict = settings.Redis.setdefault('default', {})
except:
    config = {}

RedisPool: redis.ConnectionPool = redis.ConnectionPool(
    host=config.setdefault('host', 'localhost'), port=config.setdefault('port', 6379))

_using: redis.Redis = redis.Redis(connection_pool=RedisPool)
Db: str = config.setdefault('name', 'default')


class Cache:
    def __init__(self, table: Optional[None], using: Optional[redis.Redis]=None):
        self.using = _using if not using else using
        self.table: str = table

    def add(self, key: str, value: bytes, expire: Optional[int]=None):
        key: MD5Str = self.get_md5_key(key)
        if not expire:
            expire: int = int(config.setdefault('expire', 60 * 60 * 24))
        o: RedisObject = RedisObject(expire=time.time() + expire, value=value)
        v: bytes = pickle.dumps(o)
        self.using.hset(Db, key, v)
        if self.table:
            self.using.sadd(self.table, key)

    def delete(self, key: str):
        key: MD5Str = self.get_md5_key(key)
        self.using.hdel(Db, key)
        self.using.srem(self.table, key)

    def update(self, key: str, value: bytes, expire: Optional[int]=None):
        return add(key, value, expire)

    def clear(self):
        keys = self.using.smembers(self.table)
        for key in keys:
            self.using.hdel(Db, key)
    
    def get(self, key: str) -> bytes:
        key: MD5Str = self.get_md5_key(key)
        v: bytes = self.using.hget(Db, key)
        if not v:
            return None
        o: RedisObject = pickle.loads(v)
        if time.time() > o.expire:
            self.using.hdel(Db, key)
            return None
        else:
            return o.value

    @classmethod
    def get_md5_key(cls, key: str) -> MD5Str:
        return hashlib.md5(key.encode()).hexdigest()

    @classmethod
    def delete_table_set(cls, table: str, using: Optional[redis.Redis]=None):
        using: redis.Redis = using if using else _using
        keys = using.smembers(table)
        for key in keys:
            using.hdel(Db, key)


class DjangoHttpMixin:
    
    @classmethod
    def make_request_key(request: HttpRequest) -> str:
        return request.path + json.dumps(request.POST.copy(), ensure_ascii=False) + json.dumps(
            json.loads(request.body), ensure_ascii=False
        )

    @classmethod
    def cached_response(expire: Optional[int]=None, table: Optional[str]=None, cache: Optional[Cache]=None):
        def _cached_response(func):
            @wraps(func)
            def _set_caches(request):
                resp: HttpResponse = func(request)
                try:
                    if resp.status_code == HTTPResponseStates.SUCCESS:
                        cache = cache if cache else Cache()
                        key: str = DjangoHttpMixin.make_request_key(request)
                        cache.add(key, pickle.dumps(resp))
                except:
                    pass
                return resp
            return _set_caches
        return _cached_response


class CachesMiddleware(MiddlewareMixin):

    cache: Cache = Cache()

    def process_request(self, request):
        try:
            key: str = DjangoHttpMixin.make_request_key(request)
            value = self.cache.get(request)
            if value:
                return pickle.loads(value)
        except:
            return
