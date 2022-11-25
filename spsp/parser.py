from typing import Iterable, Iterator, Type

from . import Expression
from . import Token
from .errors import SpspSyntaxError

__all__ = [
    'parse'
]


def parse_single(tokens: Iterator[Token.AnyToken]) -> Expression.AnyExpression:
    return next(it for it in _parse(tokens, at_most=1))


def parse(tokens: Iterable[Token.AnyToken]) -> Iterable[Expression.AnyExpression]:
    return _parse(iter(tokens))


def _parse(
        tokens: Iterator[Token.AnyToken],
        at_most: int | None = None,
        until: Type[Token.AnyToken] | None = None
) -> Iterable[Expression.AnyExpression]:
    parsed = 0

    token: Token.AnyToken | None = None

    while True:
        token, prev = next(tokens, None), token

        if token is None \
                or until is not None and isinstance(token, until) \
                or at_most is not None and parsed >= at_most:
            break

        match token:
            case Token.RightParenthesis() | Token.RightSquareBracket():
                raise SpspSyntaxError(token.position, f'Unexpected {token}')
            case Token.Literal(_, value):
                yield Expression.Literal(token.position, value)
            case Token.Identifier(_, name):
                yield Expression.Identifier(token.position, name)
            case Token.AttributeAccess(_, name, attributes):
                yield Expression.AttributeAccess(token.position, name, attributes)
            case Token.LeftParenthesis():
                yield Expression.Symbolic(
                    token.position,
                    operation=next(it for it in _parse(tokens, at_most=1)),
                    arguments=tuple(_parse(tokens, until=Token.RightParenthesis))
                )
            case Token.LeftSquareBracket():
                yield Expression.List(token.position, items=tuple(_parse(tokens, until=Token.RightSquareBracket)))
            case Token.EndOfStream():
                break
            case _:
                raise NotImplementedError(f'Unknown token {token}')

        parsed += 1

    if until is not None and not isinstance(token, until):
        assert token is not None
        raise SpspSyntaxError(token.position, f'Unexpected end of stream: expected {until.__name__} after {prev}')
