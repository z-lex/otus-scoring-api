import abc
import time
import typing as t
from urllib.parse import urlparse

import redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError
from redis.retry import Retry

if t.TYPE_CHECKING:
    from urllib.parse import ParseResult

DEFAULT_TIMEOUT: float = 30.0
DEFAULT_RETRY_ATTEMPTS: int = 5
DEFAULT_CACHE_TIMEOUT: float = 30.0


class StoreError(Exception):
    ...


class StoreConnectionError(StoreError):
    ...


class AbstractStore(abc.ABC):
    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
        *args,
        **kwargs,
    ):
        self._timeout = timeout
        self._retry_attempts = retry_attempts

    @abc.abstractmethod
    def get(self, key: str) -> t.Any:
        ...

    @abc.abstractmethod
    def set(self, key: str, value: t.Any) -> None:
        ...

    @abc.abstractmethod
    def cache_get(self, key: str) -> t.Any:
        ...

    @abc.abstractmethod
    def cache_set(self, key: str, value: t.Any, timeout: float) -> None:
        ...


DEFAULT_REDIS_URL: str = "redis://localhost:6379"


class RedisStore(AbstractStore):
    def __init__(
        self,
        url: str = DEFAULT_REDIS_URL,
        timeout: float = DEFAULT_TIMEOUT,
        retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    ):
        super(RedisStore, self).__init__(timeout, retry_attempts)
        self._cache = {}
        self._cache_expires = {}

        self._url: ParseResult = urlparse(url)
        self._redis = redis.Redis(
            host=self._url.hostname,
            port=self._url.port,
            username=self._url.username,
            password=self._url.password,
            socket_timeout=timeout,
            retry=Retry(ExponentialBackoff(), retries=self._retry_attempts),
        )

    @property
    def redis(self):
        return self._redis

    def get(self, key: str) -> t.Any:
        try:
            return self._redis.get(key)
        except RedisConnectionError:
            raise StoreConnectionError
        except RedisError:
            raise StoreError

    def set(self, key: str, value: t.Any) -> None:
        try:
            self._redis.set(key, value)
        except RedisConnectionError:
            raise StoreConnectionError
        except RedisError:
            raise StoreError

    def cache_get(self, key: str) -> t.Any:
        # remove from cache if expired
        if key in self._cache and time.time() > self._cache_expires[key]:
            self._cache.pop(key)
            self._cache_expires.pop(key)

        if key in self._cache:
            return self._cache[key]
        else:
            try:
                return self._redis.get(key)
            except RedisError:
                return None

    def cache_set(
        self, key: str, value: t.Any, timeout: float = DEFAULT_CACHE_TIMEOUT
    ) -> None:
        self._cache[key] = value
        self._cache_expires[key] = time.time() + timeout
