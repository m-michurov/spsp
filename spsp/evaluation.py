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
    SpspValueError, SpspInvalidBindingError
)
from .keywords import Keyword
from .special_symbols import SpecialSymbols
from .scope import Scope

__all__ = [
    'evaluate'
]


@dataclass
class Macro:
    _arguments: tuple[str, ...]
    _body: Expression.AnyExpression
    _closure_scope: Scope

    def __call__(self, *args: Any) -> Any:
        return evaluate(self._body, scope=self._bind_arguments(args))

    def __str__(self) -> str:
        return f'{SpecialSymbols.LeftParenthesis}{Keyword.Macro}' \
               f' {SpecialSymbols.LeftSquareBracket}{" ".join(self._arguments)}{SpecialSymbols.RightSquareBracket}' \
               f' {self._body}' \
               f'{SpecialSymbols.RightParenthesis}'

    def __repr__(self) -> str:
        return self.__str__()

    def _bind_arguments(self, args: Collection[Any]) -> Scope:
        local_scope = self._closure_scope.derive()

        if len(self._arguments) > len(args):
            raise SpspArityError(
                f'Not enough arguments (missing {", ".join(self._arguments[len(args):])})',
                expected=len(self._arguments),
                actual=len(args)
            )

        if len(self._arguments) < len(args):
            raise SpspArityError(
                f'Too many argument values',
                expected=len(self._arguments),
                actual=len(args)
            )

        for argument, value in zip(self._arguments, args):
            local_scope.const(argument, value)

        return local_scope


@dataclass
class Lambda:
    _arguments: Expression.List
    _body: Expression.AnyExpression
    _closure_scope: Scope

    def __call__(self, *args: Any) -> Any:
        return evaluate(self._body, scope=self._bind_arguments(args))

    def __str__(self) -> str:
        return f'{SpecialSymbols.LeftParenthesis}{Keyword.Lambda} {self._arguments} {self._body}' \
               f'{SpecialSymbols.RightParenthesis}'

    def __repr__(self) -> str:
        return self.__str__()

    def _bind_arguments(self, args: Collection[Any]) -> Scope:
        local_scope = self._closure_scope.derive()
        bind_destructuring(self._arguments, args, mutable=False, scope=local_scope)
        return local_scope


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

    return _evaluate(expression, scope)


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

    if isinstance(operation, Macro):
        generated = operation(*expression.arguments)
        return evaluate(generated, scope)

    arguments = (evaluate(it, scope) for it in expression.arguments)
    return operation(*arguments)


@special_form(Keyword.If, arity=3)
def _if(arguments: tuple[Expression.AnyExpression, ...], scope: Scope) -> Any:
    condition, when_true, when_false = arguments

    if evaluate(condition, scope):
        return evaluate(when_true, scope)

    return evaluate(when_false, scope)


def bind_destructuring(
        targets: Expression.List,
        values: Collection[Any],
        mutable: bool,
        scope: Scope
) -> None:
    if len(targets.items) > len(values):
        raise SpspInvalidBindingError(f'Not enough values to unpack (expected {len(targets.items)})')

    if len(targets.items) < len(values):
        raise SpspInvalidBindingError(f'Too many values to unpack (expected {len(targets.items)})')

    for target, value in zip(targets.items, values):
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
            bind_destructuring(target, value, mutable, scope)
            continue

        raise SpspInvalidBindingTargetError(target)


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
        bind_destructuring(target, value, mutable=True, scope=scope)
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
        raise SpspValueError(f'Function arguments list must be {Expression.List.__name__}')

    return Lambda(args, body, scope.derive())


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

    arg_identifiers: list[str] = []

    for expr in args.items:
        if not isinstance(expr, Expression.Identifier):
            raise SpspValueError(
                f'"{Keyword.Macro}" arguments list must only contain {Expression.Identifier.__name__}s'
            )

        arg_identifiers.append(expr.name)

    return Macro(tuple(arg_identifiers), body, scope.derive())
