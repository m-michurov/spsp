from typing import Any, Callable

from . import Expression
from .attribute_utility import set_attribute_value, get_attribute_value, delete_attribute_value
from .errors import SpspInvalidBindingTargetError, SpspValueError, SpspArityError
from .evaluation import evaluate
from .function import Function, Overload
from .keywords import Keyword
from .macro import Macro
from .scope import Scope
from .special_form import special_form, fixed_arguments_count, variadic
from .structural_binding import parse_structural_binding_target, bind_structural, rebind_structural

__all__ = []


@special_form(Keyword.If, fixed_arguments_count(3))
def _if(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    condition, when_true, when_false = arguments

    if evaluate(condition, scope, force_eval_lazy=True):
        return evaluate(when_true, scope)

    return evaluate(when_false, scope)


@special_form(Keyword.Let, fixed_arguments_count(2))
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


@special_form(Keyword.Rebind, fixed_arguments_count(2))
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


@special_form(Keyword.Del, fixed_arguments_count(1))
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


def collect_overloads(
        arguments: tuple[Expression.AnyExpression, ...],
        parse_signature: Callable[[Expression.List, Expression.AnyExpression], Overload],
        keyword: str) -> tuple[Overload, ...]:
    overloads: list[Overload] = []

    for signature in arguments:
        match signature:
            case Expression.Symbolic(position=_, operation=Expression.List(), arguments=(_, )):
                signature: Expression.Symbolic
                overloads.append(parse_signature(*tuple(signature)))
            case _:
                raise SpspValueError(f'"{keyword}": usage: ({keyword} <args-list> <body>) '
                                     f'or ({keyword} (<args-list> <body>) +)')

    return tuple(overloads)


@special_form(Keyword.Lambda, variadic())
def _lambda(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    def parse_signature(signature: Expression.AnyExpression) -> Overload:
        match signature:
            case Expression.Symbolic(position=_, operation=Expression.List(), arguments=(_, )):
                signature: Expression.Symbolic
                _args_expression, _body_expression = tuple(signature)

                _args = parse_structural_binding_target(_args_expression, allow_attributes=False)
                return Overload(_args, _body_expression)
            case _:
                raise SpspValueError(
                    f'"{Keyword.Lambda}": use ({Keyword.Lambda} <args-list> <body>) '
                    f'or ({Keyword.Lambda} (<args-list> <body>) +)'
                )

    match arguments:
        case (Expression.List(), _):
            args_expression, body_expression = arguments
            args_expression: Expression.List

            args = parse_structural_binding_target(args_expression, allow_attributes=False)
            return Function((Overload(args, body_expression),), scope.derive())

    return Function(
        tuple(map(parse_signature, arguments)),
        scope.derive()
    )


@special_form(Keyword.Do, variadic())
def _do(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    local_scope = scope.derive()

    result = None
    for result in (evaluate(it, local_scope) for it in arguments):
        pass

    return result


@special_form(Keyword.Expression, fixed_arguments_count(1))
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


@special_form(Keyword.EvaluateExpression, fixed_arguments_count(1))
def _eval(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    expr, = arguments

    return evaluate(evaluate(expr, scope), scope)


@special_form(Keyword.Macro, variadic())
def _macro(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    def parse_signature(signature: Expression.AnyExpression) -> Overload:
        match signature:
            case Expression.Symbolic(position=_, operation=Expression.List(), arguments=(_, )):
                signature: Expression.Symbolic
                _args_expression, _body_expression = tuple(signature)

                _args = parse_structural_binding_target(_args_expression, allow_attributes=False, allow_nested=False)
                return Overload(_args, _body_expression)
            case _:
                raise SpspValueError(
                    f'"{Keyword.Macro}": use ({Keyword.Macro} <args-list> <body>) '
                    f'or ({Keyword.Macro} (<args-list> <body>) +)'
                )

    match arguments:
        case (Expression.List(), _):
            args_expression, body_expression = arguments
            args_expression: Expression.List

            args = parse_structural_binding_target(args_expression, allow_attributes=False, allow_nested=False)
            return Macro((Overload(args, body_expression),), scope.derive())

    return Macro(
        tuple(map(parse_signature, arguments)),
        scope.derive()
    )


@special_form(Keyword.Symbolic, fixed_arguments_count(1))
def _symbolic(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    expr, = arguments
    items = evaluate(expr, scope)
    op, args = items[0], items[1:]
    return Expression.Symbolic(expr.position, op, tuple(args))
