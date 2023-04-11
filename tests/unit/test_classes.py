import typing as t
from contextlib import nullcontext as does_not_raise

import pytest

from otus_scoring_api.classes import (
    ArgumentsField,
    BirthDayField,
    CharField,
    ClientIDsField,
    ClientsInterestsRequest,
    DateField,
    EmailField,
    GenderField,
    OnlineScoreRequest,
    PhoneField,
    ValidationError,
)


# testing the 'validate' method of the different field classes
@pytest.mark.parametrize(
    "field_cls,values,expectation",
    [
        (CharField, ["value"], does_not_raise()),
        (CharField, [12345], pytest.raises(ValidationError)),
        (ArgumentsField, [{1: 2}], does_not_raise()),
        (ArgumentsField, [[1, 2, 3]], pytest.raises(ValidationError)),
        (EmailField, ["123@123"], does_not_raise()),
        (EmailField, [123, [1, 2, 3], "123"], pytest.raises(ValidationError)),
        (PhoneField, [79218677154, "79218677154"], does_not_raise()),
        (
            PhoneField,
            [
                89218677154,  # wrong first digit
                79218677154.2,  # nonzero exponent
                792186771541,  # wrong length
                "782186771543",  # wrong string length
                "7a218677154",  # wrong symbols in string
            ],
            pytest.raises(ValidationError),
        ),
        (DateField, ["02.04.1982", "05.01.2030"], does_not_raise()),
        (
            DateField,
            [
                "32.13.1999",  # wrong day and month
                "32112.19991",  # string that cannot be parsed
                12354,  # wrong type
            ],
            pytest.raises(ValidationError),
        ),
        (BirthDayField, ["02.04.1982", "05.01.1960"], does_not_raise()),
        (
            BirthDayField,
            [
                "01.01.1941",  # more than 70 years
                "20.01.2030",  # from future
            ],
            pytest.raises(ValidationError),
        ),
        (GenderField, [0, 1, 2], does_not_raise()),
        (
            GenderField,
            [3, -1, "0"],
            pytest.raises(ValidationError),
        ),
        (ClientIDsField, [[0], [1, 2]], does_not_raise()),
        (
            ClientIDsField,
            [
                [0, "1"],
                [{}, 2],
                [None, 12],
                {11: 12},
            ],
            pytest.raises(ValidationError),
        ),
    ],
)
def test_fields(field_cls: t.Type, values: t.List, expectation):
    f = field_cls()
    for val in values:
        with expectation:
            assert f.validate(val) == val


# testing instantiation of the request classes
@pytest.mark.parametrize(
    "req_class,data,expectation",
    [
        (
            ClientsInterestsRequest,
            dict(
                client_ids=[0, 1, 2],
                date="05.01.2030",
            ),
            does_not_raise(),
        ),
        (
            OnlineScoreRequest,
            dict(
                first_name="Alexey",
                last_name="Zateev",
            ),
            does_not_raise(),
        ),
    ],
)
def test_init_req(req_class: t.Type, data: t.Dict, expectation):
    with expectation:
        req = req_class(**data)
        for k, v in data.items():
            assert getattr(req, k) == v
