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


@define('+')
def _plus(arg0: Any, *args) -> Any:
    if not args:
        return operator.pos(arg0)

    return reduce(
        operator.add,
        args,
        arg0
    )


@define('-')
def _minus(arg0: Any, *args) -> Any:
    if not args:
        return operator.neg(arg0)

    return reduce(
        operator.sub,
        args,
        arg0
    )


define('*', operator.mul)
define('/', operator.truediv)
define('//', operator.floordiv)
define('**', operator.pow)
define('%', operator.mod)

define(Keyword.ImportModule, importlib.import_module)

define('first', lambda it: it[0])
define('rest', lambda it: it[1:])
define('call', lambda fn, args: fn(*args))
define('doc', lambda obj: obj.__doc__)

define('<', operator.lt)
define('<=', operator.le)
define('>', operator.gt)
define('>=', operator.ge)
define('=', operator.eq)
define('is', operator.is_)
define('is-not', operator.is_not)
define('not', operator.not_)
define('contains', operator.contains)

define('predefined', lambda: list(map(str, predefined())))

define('set', lambda obj, item, val: obj.__setitem__(item, val))
define('get', lambda obj, item: obj.__getitem__(item))
