import json
import random
import typing as t

import pytest
import redis

from otus_scoring_api.store import AbstractStore, RedisStore


@pytest.fixture
def mock_store() -> AbstractStore:
    class MockStore(AbstractStore):
        connected = True

        def get(self, key: str) -> t.Any:
            interests = [
                "cars",
                "pets",
                "travel",
                "hi-tech",
                "sport",
                "music",
                "books",
                "tv",
                "cinema",
                "geek",
                "otus",
            ]
            return json.dumps(random.sample(interests, 2))

        def set(self, key: str, value: t.Any) -> None:
            pass

        def cache_get(self, key: str) -> t.Any:
            pass

        def cache_set(self, key: str, value: t.Any, timeout: int) -> None:
            pass

    return MockStore()


@pytest.fixture(autouse=True)
def monkeypatch_redis(monkeypatch):
    class MockRedis:
        connected = True

        def __init__(self, *args, **kwargs):
            self.data = {}

        def get(self, key, *args, **kwargs):
            if not self.connected:
                raise redis.ConnectionError
            if key in self.data:
                return self.data[key]
            return None

        def set(self, key, value, *args, **kwargs):
            if not self.connected:
                raise redis.ConnectionError
            self.data[key] = value

    monkeypatch.setattr("redis.Redis", MockRedis)


@pytest.fixture
def store_with_mocked_redis() -> RedisStore:
    return RedisStore()
