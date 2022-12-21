from typing import Any

from . import Expression
from .attribute_utility import set_attribute_value, get_attribute_value, delete_attribute_value
from .errors import SpspInvalidBindingTargetError, SpspValueError, SpspArityError
from .evaluation import evaluate
from .function import Function
from .keywords import Keyword
from .macro import Macro
from .scope import Scope
from .special_form import special_form, VARIADIC
from .structural_binding import parse_structural_binding_target, bind_structural, rebind_structural

__all__ = []


@special_form(Keyword.If, arity=3)
def _if(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    condition, when_true, when_false = arguments

    if evaluate(condition, scope, force_eval_lazy=True):
        return evaluate(when_true, scope)

    return evaluate(when_false, scope)


@special_form(Keyword.Let, arity=2)
def _let(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    target_expression, value_expression = arguments

    if isinstance(target_expression, Expression.Identifier):
        value = evaluate(value_expression, scope)
        scope.let(target_expression.name, value)
        return value

    if isinstance(target_expression, Expression.AttributeAccess):
        value = evaluate(value_expression, scope)
        set_attribute_value(
            get_attribute_value(scope.value(target_expression.name), target_expression.attributes[:-1]),
            target_expression.attributes[-1],
            value,
        )
        return value

    if isinstance(target_expression, Expression.List):
        value = evaluate(value_expression, scope)
        target = parse_structural_binding_target(target_expression)

        bind_structural(target, value, mutable=True, scope=scope)
        return value

    raise SpspInvalidBindingTargetError(target_expression)


@special_form(Keyword.Rebind, arity=2)
def _rebind(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    target_expression, value_expression = arguments

    if isinstance(target_expression, Expression.Identifier):
        value = evaluate(value_expression, scope)
        scope.rebind(target_expression.name, value, mutable=True)
        return value

    if isinstance(target_expression, Expression.AttributeAccess):
        raise SpspInvalidBindingTargetError(target_expression, f'Use "{Keyword.Let}" to change attribute values')

    if isinstance(target_expression, Expression.List):
        value = evaluate(value_expression, scope)
        target_expression = parse_structural_binding_target(target_expression, allow_attributes=False)

        rebind_structural(target_expression, value, mutable=True, scope=scope)
        return value

    raise SpspInvalidBindingTargetError(target_expression)


@special_form(Keyword.Del, arity=1)
def _del(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    target, = arguments

    if isinstance(target, Expression.Identifier):
        scope.delete(target.name)
        return

    if isinstance(target, Expression.AttributeAccess):
        delete_attribute_value(
            get_attribute_value(scope.value(target.name), target.attributes[:-1]),
            target.attributes[-1]
        )
        return

    raise SpspInvalidBindingTargetError(target)


@special_form(Keyword.Lambda, arity=2)
def _lambda(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    args_expression, body_expression = arguments

    if not isinstance(args_expression, Expression.List):
        raise SpspValueError(f'"{Keyword.Lambda}" arguments list must be {Expression.List.__name__}')

    arguments = parse_structural_binding_target(args_expression, allow_attributes=False)

    return Function(arguments, body_expression, evaluate, scope.derive())


@special_form(Keyword.Do, arity=VARIADIC)
def _do(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    local_scope = scope.derive()

    result = None
    for result in (evaluate(it, local_scope) for it in arguments):
        pass

    return result


@special_form(Keyword.Expression, arity=1)
def _as_code(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    expr, = arguments

    def preprocess(_expr: Expression.AnyExpression) -> Expression.AnyExpression:
        if isinstance(_expr, Expression.Symbolic) \
                and isinstance(_expr.operation, Expression.Identifier) \
                and _expr.operation.name in (Keyword.InlineLiteral, Keyword.Inline):
            if len(_expr.arguments) != 1:
                raise SpspArityError(_expr.operation.name, expected=1, actual=len(_expr.arguments))

            if _expr.operation.name == Keyword.Inline:
                return evaluate(_expr.arguments[0], scope)

            return Expression.Literal(_expr.position, evaluate(_expr.arguments[0], scope))

        if isinstance(_expr, Expression.Symbolic):
            return Expression.Symbolic(
                _expr.position,
                preprocess(_expr.operation), tuple(map(preprocess, _expr.arguments))
            )

        if isinstance(_expr, Expression.List):
            return Expression.List(_expr.position, tuple(map(preprocess, _expr.items)))

        return _expr

    ast = preprocess(expr)
    return ast


@special_form(Keyword.EvaluateExpression, arity=1)
def _eval(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    expr, = arguments

    return evaluate(evaluate(expr, scope), scope)


@special_form(Keyword.Macro, arity=2)
def _macro(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    args_expression, body_expression = arguments

    if not isinstance(args_expression, Expression.List):
        raise SpspValueError(f'"{Keyword.Macro}" arguments list must be {Expression.List.__name__}')

    arguments = parse_structural_binding_target(args_expression, allow_nested=False, allow_attributes=False)

    return Macro(arguments, body_expression, evaluate, scope.derive())
