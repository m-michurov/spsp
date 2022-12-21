from dataclasses import dataclass
from typing import Collection, Any, Callable

from . import Expression
from .scope import Scope
from .structural_binding import StructuralBindingTarget, bind_structural

__all__ = [
    'Function'
]


@dataclass(frozen=True, repr=False)
class Function:
    _arguments: StructuralBindingTarget
    _body: Expression.AnyExpression
    _evaluate: Callable[[Expression.AnyExpression, Scope], Any]
    _closure_scope: Scope

    def __call__(self, *args: Any) -> Any:
        return self._evaluate(self._body, self._bind_arguments(args))

    @property
    def __name__(self) -> str:
        return repr(self)

    def _bind_arguments(self, args: Collection[Any]) -> Scope:
        local_scope = self._closure_scope.derive()
        bind_structural(self._arguments, args, mutable=False, scope=local_scope)
        return local_scope
