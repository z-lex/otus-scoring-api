from __future__ import annotations

import hashlib
import typing as t
from datetime import datetime

import pytest

from otus_scoring_api.constants import ADMIN_LOGIN, ADMIN_SALT, SALT
from otus_scoring_api.handlers import method_handler

if t.TYPE_CHECKING:
    from otus_scoring_api.store import AbstractStore


@pytest.fixture
def get_response(
    mock_store: AbstractStore,
) -> t.Callable[..., t.Tuple[t.Union[t.Dict, str, None], t.Optional[int]]]:
    def _func(
        req: t.Dict,
        headers: t.Optional[t.Dict] = None,
        context: t.Optional[t.Dict] = None,
    ) -> t.Tuple[t.Union[t.Dict, str, None], t.Optional[int]]:
        return method_handler(
            request={
                "body": req,
                "headers": headers if headers is not None else {},
            },
            ctx=context if context is not None else {},
            store=mock_store,
        )

    return _func


@pytest.fixture
def set_valid_auth() -> t.Callable[[t.Dict], None]:
    def _func(req_body: t.Dict) -> None:
        if req_body.get("login") == ADMIN_LOGIN:
            req_body["token"] = hashlib.sha512(
                f"{datetime.now().strftime('%Y%m%d%H')}"
                f"{ADMIN_SALT}".encode("utf-8")
            ).hexdigest()
        else:
            msg = (
                req_body.get("account", "") + req_body.get("login", "") + SALT
            ).encode("utf-8")
            req_body["token"] = hashlib.sha512(msg).hexdigest()

    return _func
