from __future__ import annotations

import typing as t

import pytest

from otus_scoring_api.store import StoreConnectionError

if t.TYPE_CHECKING:
    from otus_scoring_api.store import RedisStore


@pytest.mark.parametrize(
    "method_name,args",
    [
        pytest.param(
            "get",
            ("some_key",),
            id="store_with_mocked_redis.get w/o connection",
        ),
        pytest.param(
            "set",
            ("some_key", "value"),
            id="store_with_mocked_redis.set w/o connection",
        ),
    ],
)
def test_no_conn(
    store_with_mocked_redis: RedisStore, method_name: str, args: tuple
):
    method = getattr(store_with_mocked_redis, method_name)
    setattr(store_with_mocked_redis.redis, "connected", False)
    with pytest.raises(StoreConnectionError):
        method(*args)


def test_get_unexistent(store_with_mocked_redis: RedisStore):
    value = store_with_mocked_redis.get("unexistent_key")
    assert value is None


def test_set_and_get(store_with_mocked_redis: RedisStore):
    key, value = "some_key", "some_value"
    store_with_mocked_redis.set(key, value)
    assert store_with_mocked_redis.get(key) == value


def test_cache_get_unexistent(store_with_mocked_redis: RedisStore):
    value = store_with_mocked_redis.cache_get("unexistent_key")
    assert value is None


def test_cache_set_and_get(store_with_mocked_redis: RedisStore):
    key, value = "some_key", "some_value"
    store_with_mocked_redis.cache_set(key, value)
    assert store_with_mocked_redis.cache_get(key) == value


def test_get_from_persistent_if_not_in_cache(
    store_with_mocked_redis: RedisStore,
):
    key, value = "some_key", "some_value"
    store_with_mocked_redis.set(key, value)
    assert store_with_mocked_redis.cache_get(key) == value


def test_different_cache_and_persistent_values(
    store_with_mocked_redis: RedisStore,
):
    key, value1, value2 = "some_key", "some_value", "another_value"
    store_with_mocked_redis.set(key, value1)
    store_with_mocked_redis.cache_set(key, value2)
    assert store_with_mocked_redis.get(key) == value1
    assert store_with_mocked_redis.cache_get(key) == value2
