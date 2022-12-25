from typing import Any

from . import Expression
from .attribute_utility import get_attribute_value
from .errors import SpspEvaluationError
from .evaluation import evaluate
from .evaluation_rule import evaluation_rule
from .function import Function
from .macro import Macro
from .scope import Scope
from .special_form import special_forms

__all__ = []

NOT_FOUND = object()


@evaluation_rule(Expression.Literal)
def _literal(expression: Expression.Literal, _: Scope) -> Any:
    return expression.value


@evaluation_rule(Expression.Identifier)
def _identifier(expression: Expression.Identifier, scope: Scope) -> Any:
    return scope.value(expression.name)


@evaluation_rule(Expression.AttributeAccess)
def _attribute_access(expression: Expression.AttributeAccess, scope: Scope) -> Any:
    return get_attribute_value(scope.value(expression.name), expression.attributes)


@evaluation_rule(Expression.List)
def _list(expression: Expression.List, scope: Scope) -> Any:
    return [evaluate(it, scope) for it in expression.items]


@evaluation_rule(Expression.Symbolic)
def _symbolic_expression(expression: Expression.Symbolic, scope: Scope) -> Any:
    if isinstance(expression.operation, Expression.Identifier) \
            and (evaluate_special := special_forms.get(expression.operation.name, NOT_FOUND)) is not NOT_FOUND:
        return evaluate_special(expression.arguments, scope)

    operation = evaluate(expression.operation, scope, force_eval_lazy=True)

    try:
        if isinstance(operation, Macro):
            generated = operation(*expression.arguments)
            return evaluate(generated, scope)

        if isinstance(operation, Function):
            arguments = (evaluate(it, scope) for it in expression.arguments)
            return operation(*arguments)

    except SpspEvaluationError as e:
        raise SpspEvaluationError(e.cause, expression.position)

    arguments = (evaluate(it, scope, force_eval_lazy=True) for it in expression.arguments)

    return operation(*arguments)
