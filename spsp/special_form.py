from typing import TypeAlias, Callable, Any, Mapping

from . import Expression
from .errors import SpspArityError
from .scope import Scope

__all__ = [
    'SpecialFormEvaluationRule',
    'special_form',
    'special_forms',
    'VARIADIC'
]

VARIADIC = object()

SpecialFormEvaluationRule: TypeAlias = Callable[[tuple[Expression.AnyExpression, ...], Scope], Any]
_special_forms: dict[str, SpecialFormEvaluationRule] = {}

special_forms: Mapping[str, SpecialFormEvaluationRule] = _special_forms


def special_form(name: str, arity: int | Any) -> Callable[[SpecialFormEvaluationRule], SpecialFormEvaluationRule]:
    def decorator(_evaluator: SpecialFormEvaluationRule) -> SpecialFormEvaluationRule:
        def _evaluator_with_arity_check(
                arguments: tuple[Expression.AnyExpression, ...],
                scope: Scope
        ) -> Any:
            if arity is not VARIADIC and len(arguments) != arity:
                raise SpspArityError(name, arity, len(arguments))

            return _evaluator(arguments, scope)

        _special_forms[name] = _evaluator_with_arity_check
        return _evaluator_with_arity_check

    return decorator
