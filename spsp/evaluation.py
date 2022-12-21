from typing import Any

from . import Expression
from .errors import (
    SpspEvaluationError
)
from .evaluation_rule import evaluation_rules
from .lazy import Lazy
from .scope import Scope

__all__ = [
    'evaluate'
]

NOT_FOUND = object()


def evaluate(
        expression: Expression.AnyExpression,
        scope: Scope,
        force_eval_lazy: bool = False
) -> Any:
    if (_evaluate := evaluation_rules.get(type(expression), NOT_FOUND)) is NOT_FOUND:
        raise NotImplementedError(type(expression))

    try:
        result = _evaluate(expression, scope)
        if isinstance(result, Lazy) and force_eval_lazy:
            return result.value
        return result
    except SpspEvaluationError:
        raise
    except Exception as e:
        raise SpspEvaluationError(e, expression.position)
