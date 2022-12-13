import importlib
import operator
from functools import reduce
from typing import Mapping, Callable, Any

from .keywords import Keyword

__all__ = [
    'predefined'
]

_predefined: dict[str, Callable[[Any], Any]] = {}


def predefined() -> Mapping[str, Callable[[Any], Any]]:
    return _predefined


def define(
        operation_name: str,
        operation: Callable[[Any], Any] | None = None
) -> Callable[[Callable[[Any], Any]], Callable[[Any], Any]] | None:
    if isinstance(operation_name, str) and type(operation_name) is not str:
        operation_name = '' + operation_name

    if operation is not None:
        _predefined[operation_name] = operation

    def decorate(_operation: Callable[[Any], Any]) -> Callable[[Any], Any]:
        define(operation_name, _operation)
        return _operation

    return decorate

define(Keyword.ImportModule, importlib.import_module)

define('call', lambda fn, args: fn(*args))
define('doc', lambda obj: obj.__doc__)

define('predefined', lambda: list(map(str, predefined())))