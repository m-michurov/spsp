from typing import TypeAlias, Callable, Any, Mapping

from . import Expression
from .errors import SpspArityError
from .scope import Scope

__all__ = [
    'SpecialFormEvaluationRule',
    'special_form',
    'special_forms',
    'fixed_arguments_count',
    'variadic'
]

SpecialFormEvaluationRule: TypeAlias = Callable[[tuple[Expression.AnyExpression, ...], Scope], Any]
_special_forms: dict[str, SpecialFormEvaluationRule] = {}

special_forms: Mapping[str, SpecialFormEvaluationRule] = _special_forms

ArityCheck: TypeAlias = Callable[[str, int], None]


def special_form(
        name: str,
        arity_check: ArityCheck) -> Callable[[SpecialFormEvaluationRule], SpecialFormEvaluationRule]:
    def decorator(_evaluator: SpecialFormEvaluationRule) -> SpecialFormEvaluationRule:
        def _evaluator_with_arity_check(
                arguments: tuple[Expression.AnyExpression, ...],
                scope: Scope
        ) -> Any:
            arity_check(name, len(arguments))
            return _evaluator(arguments, scope)

        _special_forms[name] = _evaluator_with_arity_check
        return _evaluator_with_arity_check

    return decorator


def fixed_arguments_count(arguments_count: int) -> Callable[[str, int], None]:
    def _validate(name: str, n_args: int) -> None:
        if arguments_count == n_args:
            return

        raise SpspArityError(name, expected=arguments_count, actual=n_args)

    return _validate


def variadic() -> Callable[[str, int], None]:
    return lambda *_: None
