from typing import TypeAlias, Callable, Any, Type, Mapping

from . import Expression
from .scope import Scope

__all__ = [
    'EvaluationRule',
    'evaluation_rules',
    'evaluation_rule'
]

EvaluationRule: TypeAlias = Callable[[Expression.AnyExpression, Scope], Any]
_evaluators: dict[Type[Expression.AnyExpression], EvaluationRule] = {}

evaluation_rules: Mapping[Type[Expression.AnyExpression], EvaluationRule] = _evaluators


def evaluation_rule(_type: Type[Expression.AnyExpression]) -> Callable[[EvaluationRule], EvaluationRule]:
    def decorator(_evaluator: EvaluationRule) -> EvaluationRule:
        _evaluators[_type] = _evaluator
        return _evaluator

    return decorator
