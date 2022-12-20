from typing import Collection, Any, TypeAlias, Union

from . import Expression
from .scope import Scope
from .attribute_utility import set_attribute_value, get_attribute_value
from .errors import SpspValueError, SpspInvalidBindingTargetError, SpspInvalidBindingError
from .keywords import Keyword

__all__ = [
    'StructuralBindingTarget',
    'parse_structural_binding_target',
    'bind_structural',
    'rebind_structural'
]

StructuralBindingTarget: TypeAlias = \
    tuple[Union['StructuralBindingTarget', Expression.Identifier, Expression.AttributeAccess], ...]


def parse_structural_binding_target(
        target: Expression.List,
        allow_nested: bool = True,
        allow_attributes: bool = True
) -> StructuralBindingTarget:
    result: list[StructuralBindingTarget | Expression.Identifier | Expression.AttributeAccess] = []

    for item in target.items:
        if isinstance(item, Expression.Identifier):
            result.append(item)
            continue

        if isinstance(item, Expression.List):
            if not allow_nested:
                raise SpspValueError(f'Structural binding not allowed')

            result.append(parse_structural_binding_target(item))
            continue

        if isinstance(item, Expression.AttributeAccess):
            if not allow_attributes:
                raise SpspValueError(f'Attribute cannot be binding targets in this context')

            result.append(item)
            continue

        raise SpspInvalidBindingTargetError(target)

    return tuple(result)


def bind_structural(
        bind_target: StructuralBindingTarget,
        values: Collection[Any],
        mutable: bool,
        scope: Scope
) -> None:
    rest: Expression.Identifier | None = None
    variadic = is_variadic(bind_target)

    if variadic:
        bind_target, rest = split_variadic_binding_target(bind_target)

    if len(bind_target) > len(values):
        raise SpspInvalidBindingError(f'Not enough values to unpack (expected {len(bind_target)}, got {len(values)})')

    if len(bind_target) < len(values) and not variadic:
        raise SpspInvalidBindingError(f'Too many values to unpack (expected {len(bind_target)}, got {len(values)})')

    for current_target, value in zip(bind_target, values):
        current_target: StructuralBindingTarget | Expression.Identifier | Expression.AttributeAccess
        value: Collection[Any]

        if isinstance(current_target, Expression.Identifier):
            scope.bind(current_target.name, value, mutable)
            continue

        if isinstance(current_target, Expression.AttributeAccess):
            set_attribute_value(
                get_attribute_value(scope.value(current_target.name), current_target.attributes[:-1]),
                current_target.attributes[-1],
                value,
            )
            continue

        bind_structural(current_target, value, mutable, scope)

    if rest is not None:
        scope.bind(
            rest.name,
            tuple(values[len(bind_target):]),
            mutable
        )


def rebind_structural(
        bind_target: StructuralBindingTarget,
        values: Collection[Any],
        mutable: bool,
        scope: Scope
) -> None:
    variadic = is_variadic(bind_target)

    if variadic:
        raise SpspInvalidBindingError(f'Variadic rebinding not allowed')

    if len(bind_target) > len(values):
        raise SpspInvalidBindingError(f'Not enough values to unpack (expected {len(bind_target)}, got {len(values)})')

    if len(bind_target) < len(values):
        raise SpspInvalidBindingError(f'Too many values to unpack (expected {len(bind_target)}, got {len(values)})')

    for current_target, value in zip(bind_target, values):
        current_target: StructuralBindingTarget | Expression.Identifier | Expression.AttributeAccess
        value: Collection[Any]

        if isinstance(current_target, Expression.Identifier):
            scope.rebind(current_target.name, value, mutable)
            continue

        if isinstance(current_target, Expression.AttributeAccess):
            set_attribute_value(
                get_attribute_value(scope.value(current_target.name), current_target.attributes[:-1]),
                current_target.attributes[-1],
                value,
            )
            continue

        rebind_structural(current_target, value, mutable, scope)
        continue


def is_variadic(target: StructuralBindingTarget) -> bool:
    if len(target) <= 1:
        return False

    def is_variadic_marker(it: Any) -> bool:
        return isinstance(it, Expression.Identifier) and Keyword.VariadicMarker == it.name

    if any(is_variadic_marker(it) for it in target[:-2]) or is_variadic_marker(target[-1]):
        raise SpspValueError(f'Invalid "{Keyword.VariadicMarker}" usage')

    if not is_variadic_marker(target[-2]):
        return False

    rest_identifier = target[-1]
    if not isinstance(rest_identifier, Expression.Identifier):
        raise SpspInvalidBindingTargetError(rest_identifier, 'Cannot bind varargs to')

    return True


def split_variadic_binding_target(target: StructuralBindingTarget) -> (StructuralBindingTarget, Expression.Identifier):
    return target[:-2], target[-1]
