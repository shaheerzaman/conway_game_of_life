import inspect
from functools import wraps
from typing import get_type_hints, Any, List, Union


def _coerce_value(value: Any, target_type: Any) -> Any:
    origin = getattr(target_type, "__origin__", None)

    # handle generic containers like list[int]
    if origin is list and hasattr(target_type, "__args__", False):
        item_type = target_type.__args__[0]
        if isinstance(value, list):
            return [_coerce_value(item, item_type) for item in value]

    # handle union types life Union[int, str]
    if origin is Union:
        for possible_type in target_type.__args__:
            try:
                return _coerce_value(value, possible_type)
            except (TypeError, ValueError):
                continue

    # base case: attempt direct coercion
    try:
        return target_type(value)
    except (TypeError, ValueError) as e:
        raise TypeError(
            f"could not coerce {value!r} of {type(value).__name__} to {target_type}"
        ) from e


def validate_and_coerce(func):
    """
    Decorator that validates and coerces function arguments based on type hints.
    """
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        coerced_args = {}
        for name, value in bound_args.arguments.items():
            if name in type_hints:
                target_type = type_hints[name]
                if not isinstance(value, target_type):
                    try:
                        coerced_value = _coerce_value(value, target_type)
                        coerced_args[name] = coerced_value
                    except TypeError as e:
                        raise TypeError(f"Argument {name} failed validation {e}")
                else:
                    coerced_args[name] = value  # already of correct type
            else:
                coerced_args[name] = value

        return func(**coerced_args)

    return wrapper


@validate_and_coerce
def process_user_data(
    user_id: int, scores: List[int], metadata: dict, is_active: bool = True
):
    """Processes user data with strict type requirements."""
    print(f"Processing user ID: {user_id} (type: {type(user_id).__name__})")
    print(f"Scores: {scores} (item types: {[type(s).__name__ for s in scores]})")
    print(f"Is Active: {is_active} (type: {type(is_active).__name__})")
    return {"status": "processed", "id": user_id}


# Simulating data received from a JSON API (where everything might be a string)
api_data = {
    "user_id": "12345",
    "scores": ["100", "88", "95"],
    "metadata": {"source": "web"},
    "is_active": "false",  # Note: our coercer doesn't handle bool strings, so this will fail.
}

# This will work
print("--- Successful Call ---")
process_user_data(user_id="987", scores=[99.0, "85"], metadata={})

# This will raise a TypeError because "false" cannot be directly coerced to bool
print("\n--- Failing Call ---")
try:
    process_user_data(**api_data)
except TypeError as e:
    print(f"ERROR: {e}")
