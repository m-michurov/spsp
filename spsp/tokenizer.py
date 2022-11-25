from __future__ import annotations

import re
from typing import TextIO, Iterable, Literal

from . import Token
from .errors import SpspSyntaxError

__all__ = [
    'Tokenizer'
]

from .keywords import Keyword

from .special_symbols import SpecialSymbols


def parse_identifier(position: int, lexeme: str) -> Token.Identifier | Token.AttributeAccess:
    if lexeme.startswith(SpecialSymbols.QualifierSeparator):
        raise SpspSyntaxError(
            position,
            f'Identifier cannot start with {SpecialSymbols.QualifierSeparator}'
        )

    if lexeme.endswith(SpecialSymbols.QualifierSeparator):
        raise SpspSyntaxError(
            position + len(lexeme) - len(SpecialSymbols.QualifierSeparator),
            f'Identifier cannot end with {SpecialSymbols.QualifierSeparator}'
        )

    components = lexeme.split(SpecialSymbols.QualifierSeparator)

    for i, component in enumerate(components):
        lexeme_position = position + len(''.join(components[:i])) + i * len(SpecialSymbols.QualifierSeparator)
        if not component:
            raise SpspSyntaxError(
                lexeme_position,
                f'Identifier component cannot be empty'
            )

        if (pos := component.find(SpecialSymbols.Colon)) != -1:
            raise SpspSyntaxError(
                lexeme_position + pos,
                f'Identifier component cannot contain {SpecialSymbols.Colon}'
            )

        if try_parse_literal(position, component) is not None:
            raise SpspSyntaxError(lexeme_position, 'Expected identifier')

    name = components[0]

    if attributes := components[1:]:
        return Token.AttributeAccess(position, name, tuple(attributes))

    return Token.Identifier(position, name)


NUMERIC_LITERAL_REGEX = re.compile(r'[-+]? (?: \d* \. \d+ | \d+ \.? )(?: [Ee] [+-]? \d+ ) ?', re.VERBOSE)


def try_parse_number(position: int, lexeme: str) -> Token.Literal | None:
    if lexeme.isnumeric() \
            or lexeme.startswith((SpecialSymbols.Plus, SpecialSymbols.Minus)) and lexeme[1:].isnumeric():
        return Token.Literal(position, value=int(lexeme))

    if NUMERIC_LITERAL_REGEX.fullmatch(lexeme):
        return Token.Literal(position, value=float(lexeme))

    if lexeme[0].isnumeric() \
            or lexeme.startswith((SpecialSymbols.Plus, SpecialSymbols.Minus)) \
            and len(lexeme) > 1 and lexeme[1].isnumeric():
        raise SpspSyntaxError(position, 'Invalid numeric literal')

    return None


def try_parse_literal(position: int, lexeme: str) -> Token.Literal | None:
    if lexeme == Keyword.TrueLiteral:
        return Token.Literal(position, value=True)

    if lexeme == Keyword.FalseLiteral:
        return Token.Literal(position, value=False)

    if lexeme == Keyword.NoneLiteral:
        return Token.Literal(position, value=None)

    if (token := try_parse_number(position, lexeme)) is not None:
        return token

    return None


def tokenize_symbol(position: int, lexeme: str) -> Token.Literal | Token.Identifier | Token.AttributeAccess:
    if (token := try_parse_literal(position, lexeme)) is not None:
        return token

    return parse_identifier(position, lexeme)


def is_whitespace(char: str) -> bool:
    return char.isspace() or char in (SpecialSymbols.Comma, SpecialSymbols.Backslash)


def can_appear_in_symbol(char: str) -> bool:
    return not is_whitespace(char) \
           and char not in (SpecialSymbols.LeftParenthesis,
                            SpecialSymbols.RightParenthesis,
                            SpecialSymbols.LeftSquareBracket,
                            SpecialSymbols.RightSquareBracket,
                            SpecialSymbols.DoubleQuote,
                            SpecialSymbols.Semicolon)


ESCAPE_CHARACTERS = {
    r'\a': '\a',
    r'\b': '\b',
    r'\t': '\t',
    r'\n': '\n',
    r'\v': '\v',
    r'\f': '\f',
    r'\r': '\r',
    r'\0': '\0',
    r'\\': '\\',
}


def escape_character(s: str) -> str | None:
    return ESCAPE_CHARACTERS.get(s)


class Tokenizer:
    def __init__(self, stream: TextIO) -> None:
        self._stream: TextIO = stream
        self._token: Token.AnyToken | None = None
        self._stream_position: int = -1
        self._token_position: int = -1
        self._end_of_stream: bool = False
        self._next_char_buffer: list[str] = []

        self._buffer: list[str] = []

    def __iter__(self) -> Iterable[Token.AnyToken]:
        self.advance()

        while True:
            yield self.current

            if isinstance(self.current, Token.EndOfStream):
                break

            self.advance()

    @property
    def current(self) -> Token.AnyToken:
        return self._token

    def advance(self) -> None:
        self._token = self._advance()
        self._buffer.clear()
        self._read_next_char(skip_whitespace=True)

    def _advance(self) -> Token.AnyToken | None:
        if self._end_of_stream:
            return Token.EndOfStream(self._stream_position)

        while not self._char or is_whitespace(self._char):
            self._read_next_char(skip_whitespace=True)

        self._token_position = self._stream_position

        match self._char:
            case SpecialSymbols.LeftParenthesis:
                return Token.LeftParenthesis(self._token_position)
            case SpecialSymbols.RightParenthesis:
                return Token.RightParenthesis(self._token_position)
            case SpecialSymbols.LeftSquareBracket:
                return Token.LeftSquareBracket(self._token_position)
            case SpecialSymbols.RightSquareBracket:
                return Token.RightSquareBracket(self._token_position)
            case SpecialSymbols.Semicolon:
                _ = self._read_comment()
                return self._advance()
            case SpecialSymbols.DoubleQuote | SpecialSymbols.SingleQuote as quote:
                return Token.Literal(self._token_position, self._read_string_literal(quote))
            case _:
                symbol = self._read_symbol()
                return tokenize_symbol(self._token_position, symbol)

    def _read_comment(self) -> str:
        comment = ''

        while self._read_next_char() and not self._char == SpecialSymbols.Newline:
            comment += self._char

        comment = comment \
            .lstrip(SpecialSymbols.Semicolon) \
            .rstrip()

        return comment

    # TODO escape sequences
    # TODO non-printable characters inside string literals
    def _read_string_literal(self, quote: Literal[SpecialSymbols.SingleQuote, SpecialSymbols.DoubleQuote]) -> str:
        string = ''

        while True:
            if not self._read_next_char():
                raise SpspSyntaxError(self._stream_position, 'Unexpected end of file')

            if not self._char.isprintable():
                raise SpspSyntaxError(self._stream_position, 'Non-printable character in string literal')

            match self._last(2):
                case [SpecialSymbols.Backslash, _quote] if _quote == quote:
                    string += _quote
                    self._buffer.clear()
                    continue
                case [SpecialSymbols.Backslash, char]:
                    escape_sequence = SpecialSymbols.Backslash + char
                    if (char := escape_character(escape_sequence)) is None:
                        raise SpspSyntaxError(self._stream_position - 1, f'Invalid escape sequence "{escape_sequence}"')

                    string += char
                    self._buffer.clear()
                    continue
                case [_, SpecialSymbols.Backslash]:
                    continue
                case [_, _quote] if _quote == quote:
                    break

            string += self._char

        return string

    def _read_symbol(self) -> str:
        symbol = self._char

        while self._read_next_char() and can_appear_in_symbol(self._char):
            symbol += self._char

        self._unread_next_char()
        return symbol

    def _next_char(self) -> str:
        if self._next_char_buffer:
            char, self._next_char_buffer = self._next_char_buffer[0], self._next_char_buffer[1:]
            return char

        read = self._stream.read(1)

        return read

    def _unread_next_char(self) -> None:
        self._next_char_buffer.insert(0, self._char)
        self._buffer = self._buffer[:-1]
        self._stream_position -= 1

    def _read_next_char(self, skip_whitespace: bool = False) -> bool:
        while True:
            char = self._next_char()

            self._stream_position += 1

            if not char:
                self._end_of_stream = True
                break

            if not char.isspace() and not char.isprintable():
                raise SpspSyntaxError(self._stream_position, 'Invalid character')

            if not skip_whitespace or not is_whitespace(char):
                self._buffer.append(char)
                break

        return not self._end_of_stream

    @property
    def _char(self) -> str:
        if not self._buffer:
            return ''

        return self._buffer[-1]

    def _last(self, n: int) -> list[str]:
        if n > len(self._buffer):
            return [''] * (n - len(self._buffer)) + self._buffer

        return self._buffer[-n:]
