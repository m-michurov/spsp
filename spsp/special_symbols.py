from __future__ import annotations

from enum import Enum

__all__ = [
    'SpecialSymbols'
]


class SpecialSymbols(str, Enum):
    Newline = '\n'

    DoubleQuote = '"'
    SingleQuote = '\''

    Backslash = '\\'
    Comma = ','
    Semicolon = ';'

    LeftParenthesis = '('
    RightParenthesis = ')'

    LeftSquareBracket = '['
    RightSquareBracket = ']'

    DecimalSeparator = '.'
    Exponent = 'e'
    Plus = '+'
    Minus = '-'

    Colon = ':'
    QualifierSeparator = Colon * 2
