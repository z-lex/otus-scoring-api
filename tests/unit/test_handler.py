import datetime
import typing as t

import pytest

from otus_scoring_api.constants import FORBIDDEN, INVALID_REQUEST, OK


def test_empty_request(get_response: t.Callable):
    _, code = get_response({})
    assert code == INVALID_REQUEST


@pytest.mark.parametrize(
    "req_body",
    [
        {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "online_score",
            "token": "",
            "arguments": {},
        },
        {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "online_score",
            "token": "sdd",
            "arguments": {},
        },
        {
            "account": "horns&hoofs",
            "login": "admin",
            "method": "online_score",
            "token": "",
            "arguments": {},
        },
    ],
)
def test_bad_auth(get_response: t.Callable, req_body: t.Dict):
    _, code = get_response(req_body)
    assert code == FORBIDDEN


@pytest.mark.parametrize(
    "req_body",
    [
        {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "online_score",
        },
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {
            "account": "horns&hoofs",
            "method": "online_score",
            "arguments": {},
        },
    ],
)
def test_invalid_method_request(
    get_response: t.Callable,
    set_valid_auth: t.Callable,
    req_body: t.Dict,
):
    set_valid_auth(req_body)
    response, code = get_response(req_body)
    assert code == INVALID_REQUEST
    assert len(response) > 0


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"phone": "79175002040"},
        {"phone": "89175002040", "email": "stupnikov@otus.ru"},
        {"phone": "79175002040", "email": "stupnikovotus.ru"},
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": -1,
        },
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": "1",
        },
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": 1,
            "birthday": "01.01.1890",
        },
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": 1,
            "birthday": "XXX",
        },
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": 1,
            "birthday": "01.01.2000",
            "first_name": 1,
        },
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": 1,
            "birthday": "01.01.2000",
            "first_name": "s",
            "last_name": 2,
        },
        {
            "phone": "79175002040",
            "birthday": "01.01.2000",
            "first_name": "s",
        },
        {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
    ],
)
def test_invalid_score_request(
    get_response: t.Callable, set_valid_auth: t.Callable, arguments: t.Dict
):
    req_body = {
        "account": "horns&hoofs",
        "login": "h&f",
        "method": "online_score",
        "arguments": arguments,
    }
    set_valid_auth(req_body)
    response, code = get_response(req_body)
    assert code == INVALID_REQUEST
    assert len(response) > 0


@pytest.mark.parametrize(
    "arguments",
    [
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {
            "gender": 1,
            "birthday": "01.01.2000",
            "first_name": "a",
            "last_name": "b",
        },
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {
            "phone": "79175002040",
            "email": "stupnikov@otus.ru",
            "gender": 1,
            "birthday": "01.01.2000",
            "first_name": "a",
            "last_name": "b",
        },
    ],
)
def test_ok_score_request(
    get_response: t.Callable, set_valid_auth: t.Callable, arguments: t.Dict
):
    req_body = {
        "account": "horns&hoofs",
        "login": "h&f",
        "method": "online_score",
        "arguments": arguments,
    }
    set_valid_auth(req_body)
    context = {}
    response, code = get_response(req_body, context=context)
    assert code == OK
    score = response.get("score")
    assert isinstance(score, (int, float)) and score >= 0
    assert sorted(context["has"]) == sorted(arguments.keys())


def test_ok_score_admin_request(
    get_response: t.Callable,
    set_valid_auth: t.Callable,
):
    arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
    req_body = {
        "account": "horns&hoofs",
        "login": "admin",
        "method": "online_score",
        "arguments": arguments,
    }
    set_valid_auth(req_body)
    response, code = get_response(req_body)
    assert code == OK
    score = response.get("score")
    assert score == 42


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ],
)
def test_invalid_interests_request(
    get_response: t.Callable, set_valid_auth: t.Callable, arguments: t.Dict
):
    req_body = {
        "account": "horns&hoofs",
        "login": "h&f",
        "method": "clients_interests",
        "arguments": arguments,
    }
    set_valid_auth(req_body)
    response, code = get_response(req_body)
    assert code == INVALID_REQUEST
    assert len(response) > 0


@pytest.mark.parametrize(
    "arguments",
    [
        {
            "client_ids": [1, 2, 3],
            "date": datetime.datetime.today().strftime("%d.%m.%Y"),
        },
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ],
)
def test_ok_interests_request(
    get_response: t.Callable, set_valid_auth: t.Callable, arguments: t.Dict
):
    req_body = {
        "account": "horns&hoofs",
        "login": "h&f",
        "method": "clients_interests",
        "arguments": arguments,
    }
    set_valid_auth(req_body)
    context = {}
    response, code = get_response(req_body, context=context)
    assert code == OK
    assert len(arguments["client_ids"]) == len(response)
    assert all(
        v and isinstance(v, list) and all(isinstance(i, str) for i in v)
        for v in response.values()
    )
    assert context.get("nclients") == len(arguments["client_ids"])
