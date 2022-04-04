import datetime
import hashlib
import typing as t

from otus_scoring_api.classes import (
    ClientsInterestsRequest,
    MethodRequest,
    OnlineScoreRequest,
    ValidationError,
)
from otus_scoring_api.constants import (
    ADMIN_SALT,
    FORBIDDEN,
    INVALID_REQUEST,
    OK,
    SALT,
)
from otus_scoring_api.scoring import get_interests, get_score

SUPPORTED_METHODS = {
    "online_score": OnlineScoreRequest,
    "clients_interests": ClientsInterestsRequest,
}


def check_auth(request: MethodRequest):
    if request.is_admin:
        digest = hashlib.sha512(
            f"{datetime.datetime.now().strftime('%Y%m%d%H')}"
            f"{ADMIN_SALT}".encode("utf-8")
        ).hexdigest()
    else:
        digest = hashlib.sha512(
            f"{request.account}{request.login}{SALT}".encode("utf-8")
        ).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(
    request: t.Dict, ctx: t.Dict, store
) -> t.Tuple[t.Union[t.Dict, str, None], t.Optional[int]]:
    response, code = {}, OK
    # trying to parse request body
    try:
        parsed_request = MethodRequest(**request.get("body", {}))
    except ValidationError as e:
        return str(e), INVALID_REQUEST

    # checking auth
    if not check_auth(parsed_request):
        return None, FORBIDDEN

    # method arguments processing
    method_class = SUPPORTED_METHODS.get(parsed_request.method)
    if not method_class:
        return (
            f"Method '{parsed_request.method}' unsupported",
            INVALID_REQUEST,
        )
    elif not parsed_request.arguments:
        return "Method arguments required", INVALID_REQUEST

    try:
        method_args = method_class(**parsed_request.arguments)
    except ValidationError as e:
        return (
            f"Wrong arguments for method '{parsed_request.method}': {str(e)}",
            INVALID_REQUEST,
        )

    # method performing
    if parsed_request.method == "online_score":
        ctx["has"] = method_args.non_empty_fields_lst
        if parsed_request.is_admin:
            score = 42
        else:
            score = get_score(store=store, **method_args.as_dict())
        response = {"score": score}

    elif parsed_request.method == "clients_interests":
        method_args = t.cast(ClientsInterestsRequest, method_args)
        ctx["nclients"] = len(method_args.client_ids)
        if not ctx["nclients"]:
            code = INVALID_REQUEST
            response = "clients_ids list cannot be empty"
        else:
            response = {
                str(cid): get_interests(store, cid)
                for cid in method_args.client_ids
            }
    else:
        code = INVALID_REQUEST
        response = f"Method '{parsed_request.method}' unsupported"

    return response, code
