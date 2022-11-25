from functools import reduce
from typing import Any

__all__ = [
    'get_attribute_value',
    'set_attribute_value',
    'delete_attribute_value'
]

from spsp.errors import SpspAttributeError, SpspTypeError

NOT_FOUND = object()


def get_attribute_value(obj: Any, attributes: tuple[str, ...]) -> Any:
    def _get_attr(_obj: Any, _attr: str) -> Any:
        if (result := getattr(_obj, _attr, NOT_FOUND)) is not NOT_FOUND:
            return result

        raise SpspAttributeError(_obj, _attr)

    return reduce(_get_attr, attributes, obj)


def set_attribute_value(obj: Any, attribute: str, value: Any) -> Any:
    try:
        setattr(obj, attribute, value)
    except TypeError as e:
        raise SpspTypeError(*e.args)


def delete_attribute_value(obj: Any, attribute: str) -> Any:
    try:
        delattr(obj, attribute)
    except TypeError as e:
        raise SpspTypeError(*e.args)
