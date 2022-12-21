from dataclasses import dataclass
from typing import Any

from . import Expression
from .errors import SpspInvalidBindingError
from .evaluation import evaluate
from .scope import Scope
from .structural_binding import (
    StructuralBindingTarget,
    bind_structural,
    is_variadic,
    split_variadic_binding_target
)

__all__ = [
    'Function',
    'Overload'
]


@dataclass(frozen=True, repr=False)
class Overload:
    arguments: StructuralBindingTarget
    body: Expression.AnyExpression

    def accepts(self, n_args: int) -> bool:
        variadic = is_variadic(self.arguments)

        if not variadic:
            return len(self.arguments) == n_args

        arguments, _ = split_variadic_binding_target(self.arguments)
        return len(arguments) <= n_args


@dataclass(frozen=True, repr=False)
class Function:
    _overloads: tuple[Overload]
    _closure_scope: Scope

    def __call__(self, *args: Any) -> Any:
        overload = next((it for it in self._overloads if it.accepts(len(args))), None)

        if overload is None:
            raise SpspInvalidBindingError(f'No suitable overload for {len(args)} argument(s)')

        local_scope = self._closure_scope.derive()
        bind_structural(overload.arguments, args, mutable=False, scope=local_scope)
        return evaluate(overload.body, local_scope)

    @property
    def __name__(self) -> str:
        return repr(self)
