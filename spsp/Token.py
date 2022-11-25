from dataclasses import dataclass

__all__ = [
    'AnyToken',
    'LeftParenthesis',
    'RightParenthesis',
    'LeftSquareBracket',
    'RightSquareBracket',
    'Identifier',
    'Literal'
]


@dataclass(frozen=True)
class AnyToken:
    position: int


class EndOfStream(AnyToken):
    pass


class LeftParenthesis(AnyToken):
    pass


class RightParenthesis(AnyToken):
    pass


class LeftSquareBracket(AnyToken):
    pass


class RightSquareBracket(AnyToken):
    pass


@dataclass(frozen=True)
class Literal(AnyToken):
    value: int | float | bool | str | None


@dataclass(frozen=True)
class Identifier(AnyToken):
    name: str


@dataclass(frozen=True)
class AttributeAccess(AnyToken):
    object: str
    attributes: tuple[str, ...]
