from __future__ import annotations

import json
import math
import typing as t
from datetime import datetime

import pytest

from otus_scoring_api.scoring import (
    get_interests,
    get_score,
    interests_key_in_store,
    score_key_in_store,
    ScoringError,
)

if t.TYPE_CHECKING:
    from otus_scoring_api.store import RedisStore


@pytest.mark.parametrize(
    "data,result",
    [
        pytest.param(
            dict(
                phone="79311234567",
                email="123@123.ru",
                birthday=datetime(day=1, month=12, year=1971),
                gender=1,
                first_name="Ivan",
                last_name="Ivanov",
            ),
            5.0,
            id="all fields",
        ),
        pytest.param(
            dict(
                phone="79311234567",
                email="123@123.ru",
                birthday=datetime(day=1, month=12, year=1971),
                first_name="Ivan",
                last_name="Ivanov",
            ),
            3.5,
            id="no birthday-gender pair",
        ),
        pytest.param(
            dict(
                phone="79311234567",
                email="123@123.ru",
                birthday=datetime(day=1, month=12, year=1971),
                gender=1,
                last_name="Ivanov",
            ),
            4.5,
            id="no names pair",
        ),
    ],
)
def test_get_score_not_in_cache(
    store_with_mocked_redis: RedisStore, data: dict, result: float
):
    value = get_score(store=store_with_mocked_redis, **data)
    assert math.isclose(value, result)


@pytest.mark.parametrize(
    "data,value",
    [
        (
            dict(
                phone="79311234567",
                email="123@123.ru",
                birthday=datetime(day=1, month=12, year=1971),
                first_name="Ivan",
                last_name="Ivanov",
            ),
            3.21,  # unrealistic score used intentionally
        ),
    ],
)
def test_get_score_from_cache(
    store_with_mocked_redis: RedisStore, data: dict, value: float
):
    key = score_key_in_store(
        phone=data["phone"],
        birthday=data["birthday"],
        first_name=data["first_name"],
        last_name=data["last_name"],
    )
    store_with_mocked_redis.cache_set(key, value, 60)

    result = get_score(
        store=store_with_mocked_redis,
        phone=data["phone"],
        email=data["email"],
        birthday=data["birthday"],
        first_name=data["first_name"],
        last_name=data["last_name"],
    )
    assert math.isclose(value, result)


def test_get_interests(store_with_mocked_redis: RedisStore):
    cid = "sample_cid"
    value = ["cars", "pets"]

    assert get_interests(store_with_mocked_redis, cid) == []

    store_with_mocked_redis.set(interests_key_in_store(cid), json.dumps(value))

    assert get_interests(store_with_mocked_redis, cid) == value


def test_get_interests_error(store_with_mocked_redis: RedisStore):
    setattr(store_with_mocked_redis.redis, "connected", False)
    with pytest.raises(ScoringError):
        get_interests(store_with_mocked_redis, "sample_cid")
