from dataclasses import dataclass
from typing import Any, Callable, TypeAlias, Type, Collection

from . import Expression
from .attribute_utility import (
    set_attribute_value,
    get_attribute_value,
    delete_attribute_value
)
from .errors import (
    SpspArityError,
    SpspInvalidBindingTargetError,
    SpspValueError,
    SpspInvalidBindingError,
    SpspEvaluationError
)
from .keywords import Keyword
from .scope import Scope

__all__ = [
    'evaluate'
]


def check_structural_binding_target(
        target: Expression.List,
        allow_nested: bool = True
) -> None:
    for item in target.items:
        if isinstance(item, Expression.Identifier):
            continue

        if isinstance(item, Expression.List):
            if not allow_nested:
                raise SpspValueError(f'Structural binding not allowed')

            check_structural_binding_target(item)
            continue

        raise SpspInvalidBindingTargetError(target)


class Arguments:
    _target: Expression.List

    def __init__(
            self,
            target: Expression.List,
            allow_structured_binding: bool = True
    ) -> None:
        if not isinstance(target, Expression.List):
            raise SpspValueError(f'Binding target must be {Expression.List.__name__}')

        check_structural_binding_target(target, allow_structured_binding)

        self._target = target

    def bind(self, values: Collection[Any], mutable: bool, scope: Scope) -> None:
        bind_structural(self._target, values, mutable, scope)


@dataclass(frozen=True, repr=False)
class Function:
    _arguments: Arguments
    _body: Expression.AnyExpression
    _closure_scope: Scope

    def __call__(self, *args: Any) -> Any:
        return evaluate(self._body, scope=self._bind_arguments(args))

    def _bind_arguments(self, args: Collection[Any]) -> Scope:
        local_scope = self._closure_scope.derive()
        self._arguments.bind(args, mutable=False, scope=local_scope)
        return local_scope


class Macro(Function):
    pass


SpecialEvaluator: TypeAlias = Callable[[tuple[Expression.AnyExpression, ...], Scope], Any]
special_forms: dict[str, SpecialEvaluator] = {}
VARIADIC = object()


def special_form(name: str, arity: int | Any) -> Callable[[SpecialEvaluator], SpecialEvaluator]:
    def decorator(_evaluator: SpecialEvaluator) -> SpecialEvaluator:
        def _evaluator_with_arity_check(
                arguments: tuple[Expression.AnyExpression, ...],
                scope: Scope
        ) -> Any:
            if arity is not VARIADIC and len(arguments) != arity:
                raise SpspArityError(name, arity, len(arguments))

            return _evaluator(arguments, scope)

        special_forms[name] = _evaluator_with_arity_check
        return _evaluator_with_arity_check

    return decorator


Evaluator: TypeAlias = Callable[[Expression.AnyExpression, Scope], Any]
evaluators: dict[Type[Expression.AnyExpression], Evaluator] = {}


def evaluation_rule(_type: Type[Expression.AnyExpression]) -> Callable[[Evaluator], Evaluator]:
    def decorator(_evaluator: Evaluator) -> Evaluator:
        evaluators[_type] = _evaluator
        return _evaluator

    return decorator


NOT_FOUND = object()


def evaluate(
        expression: Expression.AnyExpression,
        scope: Scope
) -> Any:
    if (_evaluate := evaluators.get(type(expression), NOT_FOUND)) is NOT_FOUND:
        raise NotImplementedError(type(expression))

    try:
        return _evaluate(expression, scope)
    except SpspEvaluationError:
        raise
    except Exception as e:
        raise SpspEvaluationError(e, expression.position)


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

    operation = evaluate(expression.operation, scope)

    try:
        if isinstance(operation, Macro):
            generated = operation(*expression.arguments)
            return evaluate(generated, scope)

        if isinstance(operation, Function):
            arguments = (evaluate(it, scope) for it in expression.arguments)
            return operation(*arguments)

    except SpspEvaluationError as e:
        raise SpspEvaluationError(e.cause, expression.position)

    arguments = (evaluate(it, scope) for it in expression.arguments)
    return operation(*arguments)


@special_form(Keyword.If, arity=3)
def _if(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    condition, when_true, when_false = arguments

    if evaluate(condition, scope):
        return evaluate(when_true, scope)

    return evaluate(when_false, scope)


def is_variadic(targets: Expression.List) -> (bool, Expression.Identifier | None):
    if len(targets.items) <= 1:
        return False, None

    marker = targets.items[-2]
    if not isinstance(marker, Expression.Identifier) or Keyword.VariadicMarker != marker.name:
        return False, None

    rest = targets.items[-1]
    if not isinstance(rest, Expression.Identifier):
        raise SpspInvalidBindingTargetError(rest, 'Cannot bind varargs to')

    return True, rest


def bind_structural(
        target_expression: Expression.List,
        values: Collection[Any],
        mutable: bool,
        scope: Scope
) -> None:
    variadic, rest_identifier = is_variadic(target_expression)

    targets = target_expression.items[:-2] if variadic else target_expression.items

    if len(targets) > len(values):
        raise SpspInvalidBindingError(f'Not enough values to unpack (expected {len(target_expression.items)})')

    if len(targets) < len(values) and not variadic:
        raise SpspInvalidBindingError(f'Too many values to unpack (expected {len(target_expression.items)})')

    for target, value in zip(targets, values):
        if isinstance(target, Expression.Identifier):
            scope.bind(target.name, value, mutable)
            continue

        if isinstance(target, Expression.AttributeAccess):
            set_attribute_value(
                get_attribute_value(scope.value(target.name), target.attributes[:-1]),
                target.attributes[-1],
                value,
            )
            continue

        if isinstance(target, Expression.List):
            bind_structural(target, value, mutable, scope)
            continue

        raise SpspInvalidBindingTargetError(target)

    if rest_identifier is not None:
        scope.bind(
            rest_identifier.name,
            tuple(values[len(targets):]),
            mutable
        )


@special_form(Keyword.Let, arity=2)
def _let(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    target, value_expression = arguments

    if isinstance(target, Expression.Identifier):
        value = evaluate(value_expression, scope)
        scope.let(target.name, value)
        return value

    if isinstance(target, Expression.AttributeAccess):
        value = evaluate(value_expression, scope)
        set_attribute_value(
            get_attribute_value(scope.value(target.name), target.attributes[:-1]),
            target.attributes[-1],
            value,
        )
        return value

    if isinstance(target, Expression.List):
        value = evaluate(value_expression, scope)
        bind_structural(target, value, mutable=True, scope=scope)
        return value

    raise SpspInvalidBindingTargetError(target)


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
    args, body = arguments

    if not isinstance(args, Expression.List):
        raise SpspValueError(f'"{Keyword.Lambda}" arguments list must be {Expression.List.__name__}')

    return Function(Arguments(args), body, scope.derive())


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
    args, body = arguments

    if not isinstance(args, Expression.List):
        raise SpspValueError(f'"{Keyword.Macro}" arguments list must be {Expression.List.__name__}')

    return Macro(
        Arguments(args, allow_structured_binding=False),
        body,
        scope.derive()
    )
