from __future__ import annotations

from builtins import *
from dataclasses import dataclass
from typing import Any

from .special_symbols import SpecialSymbols

__all__ = [
    'AnyExpression',
    'List',
    'Symbolic',
    'Literal',
    'Identifier',
    'AttributeAccess'
]

NOT_FOUND = object()


@dataclass(frozen=True)
class AnyExpression:
    position: int

    @property
    def code(self) -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        return self.code

    def __repr__(self) -> str:
        return self.__str__()


@dataclass(frozen=True)
class Symbolic(AnyExpression):
    operation: AnyExpression
    arguments: tuple[AnyExpression, ...]

    def __getitem__(self, item: int | slice) -> AnyExpression:
        return ((self.operation,) + self.arguments)[item]

    @property
    def code(self) -> str:
        return \
            SpecialSymbols.LeftParenthesis \
            + self.operation.code \
            + ' ' \
            + ' '.join(it.code for it in self.arguments) \
            + SpecialSymbols.RightParenthesis


@dataclass(frozen=True)
class List(AnyExpression):
    items: tuple[AnyExpression, ...]

    @property
    def code(self) -> str:
        return \
            SpecialSymbols.LeftSquareBracket \
            + ' '.join(it.code for it in self.items) \
            + SpecialSymbols.RightSquareBracket


# noinspection DuplicatedCode
@dataclass(frozen=True)
class Literal(AnyExpression):
    value: Any | None

    @property
    def code(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Identifier(AnyExpression):
    name: str

    @property
    def code(self) -> str:
        return self.name


@dataclass(frozen=True)
class AttributeAccess(AnyExpression):
    name: str
    attributes: tuple[str, ...]

    @property
    def code(self) -> str:
        return SpecialSymbols.QualifierSeparator.join((self.name,) + self.attributes)
