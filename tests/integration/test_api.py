from __future__ import annotations

import json
import math
import typing as t

import redis.exceptions
import requests

from otus_scoring_api.constants import FORBIDDEN, OK
from otus_scoring_api.scoring import interests_key_in_store


def test_bad_auth(api_url: str, request_headers: dict):
    req_body = {
        "account": "horns&hoofs",
        "login": "h&f",
        "method": "online_score",
        "token": "",
        "arguments": {},
    }
    resp = requests.post(api_url, headers=request_headers, json=req_body)
    assert resp.status_code == FORBIDDEN


def test_method_online_score(
    api_url: str,
    request_headers: dict,
    set_valid_auth: t.Callable,
):
    req_body = {
        "account": "horns&hoofs",
        "login": "h&f",
        "method": "online_score",
        "arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru"},
    }
    set_valid_auth(req_body)
    resp = requests.post(api_url, headers=request_headers, json=req_body)

    assert resp.status_code == OK

    resp_body = resp.json()
    assert resp_body["code"] == resp.status_code
    assert isinstance(resp_body["response"], dict)
    assert math.isclose(resp_body["response"]["score"], 3.0)


def test_method_clients_interests(
    api_url: str,
    redis_instance: redis.Redis,
    request_headers: dict,
    set_valid_auth: t.Callable,
):
    cid = 123
    value = ["cars", "pets"]

    # prepare redis
    redis_key = interests_key_in_store(str(cid))
    redis_instance.set(redis_key, json.dumps(value))

    req_body = {
        "account": "horns&hoofs",
        "login": "h&f",
        "method": "clients_interests",
        "arguments": {"client_ids": [cid]},
    }
    set_valid_auth(req_body)

    resp = requests.post(api_url, headers=request_headers, json=req_body)

    assert resp.status_code == OK

    resp_body = resp.json()
    assert resp_body["code"] == resp.status_code
    assert isinstance(resp_body["response"], dict)
    assert str(cid) in resp_body["response"]
    assert resp_body["response"][str(cid)] == value

    # cleanup redis data
    redis_instance.delete(redis_key)
