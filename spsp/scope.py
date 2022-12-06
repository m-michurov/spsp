from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import cache
from types import ModuleType
from typing import Any

from .errors import (
    SpspNameError,
    SpspInvalidBindingTargetError
)
from .keywords import Keyword
from .predefined import predefined

__all__ = [
    'Scope'
]

PYTHON_BUILTINS = 'builtins'

NOT_FOUND = object()


class BindingType(Enum):
    Constant = auto()
    Variable = auto()


@dataclass(frozen=True)
class Binding:
    value: Any
    type: BindingType


@dataclass(frozen=True)
class Scope:
    _bindings: dict[str, Binding] = field(default_factory=lambda: {
        name: Binding(value, BindingType.Constant)
        for name, value in predefined().items()
    }, hash=False)
    _module_cache: dict[str, ModuleType] = field(default_factory=lambda: {
        PYTHON_BUILTINS: importlib.import_module(PYTHON_BUILTINS)
    }, hash=False)

    _outer: Scope | None = None

    def _copy(self) -> Scope:
        return Scope(
            _bindings=self._bindings.copy(),
            _module_cache=self._module_cache.copy(),
            _outer=self._outer
        )

    @property
    @cache
    def _builtins(self) -> ModuleType:
        return self._module_cache[PYTHON_BUILTINS]

    def import_module(self, module_name: str) -> ModuleType:
        if (module := self._module_cache.get(module_name)) is not None:
            return module

        module = \
            importlib.import_module(module_name) if self._outer is None else self._outer.import_module(module_name)

        self._module_cache[module_name] = module
        return module

    @staticmethod
    def empty() -> Scope:
        return Scope()

    def let(self, name: str, value: Any) -> None:
        self._bind_name(name, value, binding_type=BindingType.Variable)

    def const(self, name: str, value: Any) -> None:
        self._bind_name(name, value, binding_type=BindingType.Constant)

    def bind(self, name: str, value: Any, mutable: bool) -> None:
        return self._bind_name(
            name,
            value,
            binding_type=BindingType.Variable if mutable else BindingType.Constant
        )

    def delete(self, name: str) -> None:
        self._unbind_value(name)

    def value(self, name: str) -> Any:
        return self._get_value(name)

    def derive(self) -> Scope:
        # return Scope(_outer=self._copy())
        return Scope(_outer=self)

    def _bind_name(
            self,
            name: str,
            value: Any,
            binding_type: BindingType
    ) -> None:
        if name in Keyword.__members__.values():
            raise SpspInvalidBindingTargetError(target=name, why='Cannot bind to keyword')

        if (existing := self._bindings.get(name, NOT_FOUND)) is NOT_FOUND:
            self._bindings[name] = Binding(value, binding_type)
            return

        if existing.type is BindingType.Constant:
            raise SpspInvalidBindingTargetError(target=name, why='Cannot rebind constant')

        self._bindings[name] = Binding(value, binding_type)

    def _unbind_value(self, name: str) -> None:
        if name in Keyword.__members__.values():
            raise SpspInvalidBindingTargetError(target=name, why='Cannot unbind keyword')

        if name in predefined():
            raise SpspInvalidBindingTargetError(target=name, why='Cannot unbind predefined')

        self._bindings.pop(name, None)

    def _get_value(self, name: str) -> Any:
        if (identifier := self._bindings.get(name, NOT_FOUND)) is not NOT_FOUND:
            return identifier.value

        if self._outer is not None:
            return self._outer._get_value(name)

        if (value := getattr(self._builtins, name, NOT_FOUND)) is not NOT_FOUND:
            return value

        raise SpspNameError(name)
