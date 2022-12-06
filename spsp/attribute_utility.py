from functools import reduce
from typing import Any

__all__ = [
    'get_attribute_value',
    'set_attribute_value',
    'delete_attribute_value'
]


def get_attribute_value(obj: Any, attributes: tuple[str, ...]) -> Any:
    return reduce(getattr, attributes, obj)


def set_attribute_value(obj: Any, attribute: str, value: Any) -> Any:
    setattr(obj, attribute, value)


def delete_attribute_value(obj: Any, attribute: str) -> Any:
    delattr(obj, attribute)
