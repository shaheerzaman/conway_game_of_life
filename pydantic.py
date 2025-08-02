import typing
from functools import wraps
from inspect import signature
from collections import defaultdict


class ValidationError(Exception):
    pass


def _coerce_and_validate(field_name, field_type, value):
    origin = typing.get_origin(field_type)

    if origin is typing.Union and type(None) in typing.get_args(field_type):
        if value is None:
            return None

        field_type = [t for t in typing.get_args(field_type) if t is not type[None]][0]

    try:
        return field_type(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f"could not convert value {value} to type {field_type} for field {field_name}"
        )


_VALIDATOR_MAP_ATTR = "__validators__"


def validator(*field_names):
    def decorator(func):
        setattr(func, _VALIDATOR_MAP_ATTR, field_names)
        return func

    return decorator


class ModelMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        schema = {}
        hints = typing.get_type_hints(attrs.get("__annotations__"))
        for field_name, field_type in hints.items():
            schema[field_name] = field_type

        attrs["__schema__"] = schema

        custom_validators = defaultdict(list)
        for attr_name, attr_value in attrs.items():
            if hasattr(attr_value, _VALIDATOR_MAP_ATTR):
                field_names_to_validate = getattr(attr_value, _VALIDATOR_MAP_ATTR)
                for field_name in field_names_to_validate:
                    custom_validators[field_name].append(attr_value)

        attrs["__custom_validators__"] = custom_validators

        return super().__new__(mcs, name, bases, attrs)


class BaseModel(metaclass=ModelMetaclass):
    def __init__(self, **kwargs):
        validated_data = {}

        for field_name, field_type in self.__schema__.items():
            value = kwargs.get(field_name)

            if value is None:
                if typing.get_origin(field_type) is not typing.Union or type(
                    None
                ) not in typing.get_args(field_type):
                    raise ValidationError(f"Missing required field: {field_name}")

            coerced_value = _coerce_and_validate(field_name, field_type, value)

            if field_name in self.__custom_validators__:
                for validaror_func in self.__custom_validators__[field_name]:
                    coerced_value = validaror_func(self, coerced_value)

            validated_data[field_name] = coerced_value

        for key, value in validated_data.items():
            object.__setattr__(self, key, value)

    def __setattr__(self, name, value):
        if name not in self.__schema__:
            super().__setattr__(name, value)
            return

        field_type = self.__schema__[name]
        coerced_value = _coerce_and_validate(name, field_type, value)
        if name in self.__custom_validators__:
            for validator_fun in self.__custom_validators__[name]:
                coerced_value = validator_fun(self, coerced_value)

        object.__setattr__(self, name, coerced_value)

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}{attrs}"


class User(BaseModel):
    user_id: int
    email: str
    is_active: bool = True
    signup_ts: typing.Optional[str] = None

    @validator("email")
    def validate_email_format(self, email_value):
        if "@" not in email_value:
            raise ValidationError(f"Invalid email format for {email_value}")
        return email_value.lower()
