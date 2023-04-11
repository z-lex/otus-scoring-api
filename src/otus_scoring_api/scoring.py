from __future__ import annotations

import datetime
import hashlib
import json
import logging
import typing as t

from otus_scoring_api.store import StoreError

if t.TYPE_CHECKING:
    from otus_scoring_api.store import AbstractStore

_logger = logging.Logger(__name__)


class ScoringError(Exception):
    ...


def score_key_in_store(
    phone: t.Union[str, int],
    birthday: t.Optional[datetime.datetime] = None,
    first_name: t.Optional[str] = None,
    last_name: t.Optional[str] = None,
) -> str:
    key_parts = [
        first_name or "",
        last_name or "",
        str(phone) or "",
        birthday.strftime("%Y%m%d") if birthday is not None else "",
    ]
    return "uid:" + hashlib.md5("".join(key_parts).encode("utf-8")).hexdigest()


def get_score(
    store: AbstractStore,
    phone: t.Union[str, int],
    email: str,
    birthday: t.Optional[datetime.datetime] = None,
    gender: t.Optional[int] = None,
    first_name: t.Optional[str] = None,
    last_name: t.Optional[str] = None,
) -> int:
    key = score_key_in_store(phone, birthday, first_name, last_name)
    # try get from cache,
    # fallback to heavy calculation in case of cache miss
    score = store.cache_get(key) or 0
    if score:
        return score
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    # cache for 60 minutes
    store.cache_set(key, score, 60 * 60)
    return score


def interests_key_in_store(cid: str) -> str:
    return "i:%s" % cid


def get_interests(
    store: AbstractStore,
    cid: str,
) -> t.List[str]:
    try:
        r = store.get(interests_key_in_store(cid))
    except StoreError as e:
        raise ScoringError(f"Can't get interests for {cid} from store: {e}")

    return json.loads(r) if r else []
