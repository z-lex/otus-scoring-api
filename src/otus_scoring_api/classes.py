import abc
import decimal
import typing as t
from datetime import datetime

from otus_scoring_api.constants import ADMIN_LOGIN


class ValidationError(ValueError):
    pass


class Field(abc.ABC):
    VALUE_TYPE: t.Type = object
    required: bool
    nullable: bool

    def __init__(self, required: bool = False, nullable: bool = True):
        if not required and not nullable:
            raise ValueError(
                f"{self.__class__.__name__}: field cannot be "
                f"optional and non-nullable at the same time"
            )
        self.required = required
        self.nullable = nullable

    def validate(self, value: t.Any) -> t.Any:
        if not self.nullable and value is None:
            raise ValidationError("Value cannot be None")

        if value and not isinstance(value, self.VALUE_TYPE):
            raise ValidationError("Wrong value type")

        return value


class CharField(Field):
    VALUE_TYPE: t.Type = str


class ArgumentsField(Field):
    VALUE_TYPE: t.Type = dict


class EmailField(CharField):
    def validate(self, value: t.Optional[str]) -> t.Optional[str]:
        v = super(EmailField, self).validate(value)
        if v and "@" not in v:
            raise ValidationError("email must contain the symbol '@'")
        return v


class PhoneField(Field):
    def validate(
        self, value: t.Union[str, int, None]
    ) -> t.Union[str, int, None]:
        v = super(PhoneField, self).validate(value)
        if v is None:
            return v

        if type(v) not in [str, int]:
            raise ValidationError("phone number must be str or int")

        try:
            dtp = decimal.Decimal(v).as_tuple()
            assert dtp.sign == 0
            assert dtp.exponent == 0
            assert len(dtp.digits) == 11
            assert dtp.digits[0] == 7
        except (decimal.DecimalException, AssertionError):
            raise ValidationError(
                "phone number must contain 11 digits and start with 7"
            )

        return v


class DateField(CharField):
    _FORMAT = "%d.%m.%Y"

    def validate(self, value: t.Optional[str]) -> t.Optional[str]:
        v = super(DateField, self).validate(value)
        if v is None:
            return v
        try:
            datetime.strptime(value, self._FORMAT)
        except ValueError:
            raise ValidationError(
                f"string '{value}' does not match with "
                f"'DD.MM.YYYY' date format"
            )
        else:
            return value


class BirthDayField(DateField):
    def validate(self, value: t.Optional[str]) -> t.Optional[str]:
        v = super(BirthDayField, self).validate(value)
        if v is None:
            return v

        today = datetime.today()
        if datetime.strptime(value, self._FORMAT) < today.replace(
            year=today.year - 70
        ):
            raise ValidationError(
                f"date of birth cannot be earlier than 70 years before now: "
                f"'{value}'"
            )
        elif datetime.strptime(value, self._FORMAT) > today:
            raise ValidationError(
                f"date of birth cannot be in future: '{value}'"
            )
        return v


class GenderField(Field):
    VALUE_TYPE: t.Type = int

    def validate(self, value: t.Optional[int]) -> t.Optional[int]:
        v = super(GenderField, self).validate(value)
        if v is not None and v not in [0, 1, 2]:
            raise ValidationError("gender field must have value 0, 1 or 2")
        return v


class ClientIDsField(Field):
    VALUE_TYPE: t.Type = list

    def validate(self, value: t.Optional[list]) -> t.Optional[list]:
        v = super(ClientIDsField, self).validate(value)
        if v is not None and not all([isinstance(_id, int) for _id in v]):
            raise ValidationError("client IDs must be of integer type")
        return v


class BaseRequest(abc.ABC):
    _fields: t.ClassVar[t.Dict[str, Field]] = {}
    _field_values: t.Dict[str, t.Any]

    def __new__(cls, *args, **kwargs):
        # update fields meta information if necessary
        if not cls._fields:
            cls._fields = {
                k: v for k, v in cls.__dict__.items() if isinstance(v, Field)
            }

        obj = object.__new__(cls)
        object.__setattr__(obj, "_field_values", cls.validate(kwargs))
        return obj

    @classmethod
    def validate(cls, data: t.Dict[str, t.Any]) -> t.Dict:
        values = {}

        # check for required fields
        for k, v in cls._fields.items():
            if k not in data.keys():
                if v.required:
                    raise ValidationError(
                        f"The value of the mandatory field '{k}' is missing"
                    )
                else:
                    values[k] = None

        for k, v in data.items():
            field = cls._fields.get(k)
            if not field:
                raise ValidationError(f"Unknown field '{k}'")
            values[k] = field.validate(v)

        return values

    @property
    def non_empty_fields_lst(self) -> t.List[str]:
        return [
            k
            for k, v in object.__getattribute__(self, "_field_values").items()
            if v is not None and v != ""
        ]

    def as_dict(self) -> t.Dict:
        return object.__getattribute__(self, "_field_values")

    def __getattribute__(self, item: str) -> t.Any:
        # return field value instead of field instance
        fields = object.__getattribute__(self, "_fields")
        if item in fields.keys():
            try:
                return object.__getattribute__(self, "_field_values")[item]
            except KeyError:
                raise AttributeError()
        else:
            return object.__getattribute__(self, item)

    def __setattr__(self, key, value):
        # validate and set field value
        field = object.__getattribute__(self, "_fields").get(key)
        if not field:
            object.__setattr__(self, key, value)
            return
        object.__getattribute__(self, "_field_values")[key] = field.validate(
            value
        )


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    @classmethod
    def validate(cls, data: t.Dict[str, t.Any]) -> t.Dict:
        values = super(OnlineScoreRequest, cls).validate(data)

        has_phone_email_pair = all([values.get("phone"), values.get("email")])
        has_names_pair = all(
            [values.get("first_name"), values.get("last_name")]
        )
        has_gender_bday_pair = all(
            [values.get("gender") is not None, values.get("birthday")]
        )
        if not any(
            [
                has_phone_email_pair,
                has_names_pair,
                has_gender_bday_pair,
            ]
        ):
            raise ValidationError(
                "request must contain at least on of the following non-empty"
                "value pairs: phone-email, first_name-last_name or "
                "gender-birthday"
            )

        return values


class MethodRequest(BaseRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN
