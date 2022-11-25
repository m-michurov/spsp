import io
from typing import Type

import pytest

from spsp import Tokenizer, Token, SpspSyntaxError


# noinspection DuplicatedCode
class TestTokenizer:
    @pytest.mark.parametrize(
        'input_string, expected',
        [
            (r'""', Token.Literal(0, '')),
            (r'"abc"', Token.Literal(0, 'abc')),
            (r'" abc "', Token.Literal(0, ' abc ')),
            (r'" a \" bc "', Token.Literal(0, ' a " bc ')),
            (r"''", Token.Literal(0, '')),
            (r"'abc'", Token.Literal(0, 'abc', )),
            (r"' abc '", Token.Literal(0, ' abc ')),
            (r"' a \' bc '", Token.Literal(0, ' a \' bc ')),
            (r"' a\\bc '", Token.Literal(0, r' a\bc ')),
        ]
    )
    def test_string_literal(self, input_string: str, expected: Token.AnyToken) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            tokenizer.advance()
            token = tokenizer.current

            # Assert
            assert token == expected

    @pytest.mark.parametrize(
        'input_string, expected',
        [
            ('True', True),
            ('False', False)
        ]
    )
    def test_bool_literal(self, input_string: str, expected: bool) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            tokenizer.advance()
            token = tokenizer.current

            # Assert
            assert isinstance(token, Token.Literal)
            assert token.value == expected

    def test_none_literal(self) -> None:
        with io.StringIO('None') as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            tokenizer.advance()
            token = tokenizer.current

            # Assert
            assert isinstance(token, Token.Literal)
            assert token.value is None

    @pytest.mark.parametrize(
        'input_string, expected_error_position',
        [
            ('"a\t"', 2),
            ('"\aa"', 1),
            ('"a\0"', 2)
        ]
    )
    def test_invalid_characters_in_string_literal(self, input_string: str, expected_error_position: int) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            with pytest.raises(SpspSyntaxError) as syntax_error:
                list(tokenizer)

            # Assert
            assert syntax_error.value.position == expected_error_position

    @pytest.mark.parametrize(
        'input_string, expected_error_position',
        [
            ('\a', 0),
            ('"abc"\a', 5),
            (' "ab\a"', 4)
        ]
    )
    def test_non_printable_character(self, input_string: str, expected_error_position: int) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            with pytest.raises(SpspSyntaxError) as syntax_error:
                list(tokenizer)

            # Assert
            assert syntax_error.value.position == expected_error_position

    def test_whitespace_between_tokens(self) -> None:
        with io.StringIO(' " abc"\n,1 \t,\r\\a::b,') as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            tokens: list[Token.AnyToken] = list(tokenizer)

            # Assert
            assert tokens[:-1] == [
                Token.Literal(1, value=' abc'),
                Token.Literal(9, value=1),
                Token.AttributeAccess(15, object='a', attributes=('b',))
            ]
            assert isinstance(tokens[-1], Token.EndOfStream)

    @pytest.mark.parametrize(
        'input_string, expected',
        [
            (r'"a"1', [
                Token.Literal(0, value='a'),
                Token.Literal(3, value=1),
            ]),
            (r'-3"a"', [
                Token.Literal(0, value=-3),
                Token.Literal(2, value='a'),
            ]),
            (r'"a"a::b', [
                Token.Literal(0, value='a'),
                Token.AttributeAccess(3, object='a', attributes=('b',)),
            ]),
            (r'"a"a::b+3', [
                Token.Literal(0, value='a'),
                Token.AttributeAccess(3, object='a', attributes=('b+3',)),
            ]),
            (r'(a::b]', [
                Token.LeftParenthesis(0),
                Token.AttributeAccess(1, object='a', attributes=('b',)),
                Token.RightSquareBracket(5)
            ]),
            (r'+3(.1e9]', [
                Token.Literal(0, value=3),
                Token.LeftParenthesis(2),
                Token.Literal(3, value=1e8),
                Token.RightSquareBracket(7)
            ]),
        ]
    )
    def test_no_whitespace_between_tokens(self, input_string: str, expected: list[Token.AnyToken]) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            tokens: list[Token.AnyToken] = list(tokenizer)

            assert tokens[:-1] == expected
            assert isinstance(tokens[-1], Token.EndOfStream)

    @pytest.mark.parametrize(
        'input_string, expected_type',
        [
            (r'1', int),
            (r'-3', int),
            (r'+42', int),
            (r'-0', int),
            (r'+0', int),
            (r'666', int),
            ('1e2', float),
            ('.02', float),
            ('02.', float),
            ('2.1', float),
            ('1e-2', float),
            ('1e+2', float),
            ('1.e-2', float),
            ('1.1e-2', float),
            ('.1e-2', float),
            ('3.', float),
            ('-1e2', float),
            ('+.02', float),
            ('-02.', float),
            ('+2.1', float),
            ('-1e-2', float),
            ('+1e+2', float),
            ('-1.e-2', float),
            ('+1.1e-2', float),
            ('-.1e-2', float),
            ('+3.', float),
        ]
    )
    def test_numeric_literal(self, input_string: str, expected_type: Type[int | float]) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            tokenizer.advance()
            token = tokenizer.current

            # Assert
            assert isinstance(token, Token.Literal)
            assert token.position == 0
            assert token.value == expected_type(input_string)

    @pytest.mark.parametrize(
        'input_string, expected_error_position',
        [
            ('+3a', 0),
            ('1.0eabc', 0),
            ('   -1a', 3),
            ('   1a', 3),
        ]
    )
    def test_invalid_numeric_literal(self, input_string: str, expected_error_position: int) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            with pytest.raises(SpspSyntaxError) as syntax_error:
                list(tokenizer)

            # Assert
            assert syntax_error.value.position == expected_error_position

    @pytest.mark.parametrize(
        'input_string, expected_name',
        [
            (r'/', '/'),
            (r'+', '+'),
            (r'abc.def', 'abc.def'),
            (r'T.T', 'T.T'),
            (r'O_o', 'O_o'),
        ]
    )
    def test_identifier(self, input_string: str, expected_name: str) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            tokenizer.advance()
            token = tokenizer.current

            # Assert
            assert isinstance(token, Token.Identifier)
            assert token.position == 0
            assert token.name == expected_name

    @pytest.mark.parametrize(
        'input_string, expected_error_position',
        [
            (r':abc', 0),
            (r'::abc', 0),
            (r'abc::', 3),
            (r'abc:', 3),
        ]
    )
    def test_invalid_identifier(self, input_string: str, expected_error_position: int) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            with pytest.raises(SpspSyntaxError) as syntax_error:
                list(tokenizer)

            # Assert
            assert syntax_error.value.position == expected_error_position

    @pytest.mark.parametrize(
        'input_string, expected_object, expected_attributes',
        [
            (r'a::b::c', 'a', ('b', 'c')),
            (r'a::b+3', 'a', ('b+3',)),
            (r'numpy.linalg::solve', 'numpy.linalg', ('solve',)),
            ('list::__doc__', 'list', ('__doc__',))
        ]
    )
    def test_attribute_access(
            self, input_string: str,
            expected_object: str,
            expected_attributes: tuple[str, ...]
    ) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            tokenizer.advance()
            token = tokenizer.current

            # Assert
            assert isinstance(token, Token.AttributeAccess)
            assert token.position == 0
            assert token.object == expected_object
            assert token.attributes == expected_attributes

    @pytest.mark.parametrize(
        'input_string, expected_error_position',
        [
            (r'a:::bc', 3),
            (r'a::::bc', 3),
            (r'a::None::bc', 3),
            (r'a::+3::bc', 3),
            (r'a::False::bc', 3),
            (r'a::"abc"::bc', 1),
            (r'"abc"::bc', 5),
            (r'abc::"abc"', 3),
        ]
    )
    def test_invalid_attribute_access(self, input_string: str, expected_error_position: int) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            with pytest.raises(SpspSyntaxError) as syntax_error:
                list(tokenizer)

            # Assert
            assert syntax_error.value.position == expected_error_position


    @pytest.mark.parametrize(
        'input_string, expected',
        [
            (r'(', [Token.LeftParenthesis(0)]),
            (r')', [Token.RightParenthesis(0)]),
            (r'[', [Token.LeftSquareBracket(0)]),
            (r']', [Token.RightSquareBracket(0)]),
            (r'([])[(])', [
                Token.LeftParenthesis(0),
                Token.LeftSquareBracket(1),
                Token.RightSquareBracket(2),
                Token.RightParenthesis(3),
                Token.LeftSquareBracket(4),
                Token.LeftParenthesis(5),
                Token.RightSquareBracket(6),
                Token.RightParenthesis(7),
            ]),
        ]
    )
    def test_parenthesis(self, input_string: str, expected: list[Token.AnyToken]) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            tokens: list[Token.AnyToken] = list(tokenizer)

            # Assert
            assert tokens[:-1] == expected
            assert isinstance(tokens[-1], Token.EndOfStream)

    @pytest.mark.parametrize(
        'input_string, expected',
        [
            ('; 1', [Token.EndOfStream(3)]),
            ('; 1 ', [Token.EndOfStream(4)]),
            ('1;;;;; 1 ;\n42', [Token.Literal(0, value=1), Token.Literal(11, value=42), Token.EndOfStream(13)]),
        ]
    )
    def test_comment(self, input_string: str, expected: list[Token.AnyToken]) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            tokens: list[Token.AnyToken] = list(tokenizer)

            # Assert
            assert tokens == expected

    @pytest.mark.parametrize(
        'input_string, expected_error_position',
        [
            ('"abc', 4),
            ("'\\' abc 123 \" ", 14),
        ]
    )
    def test_unexpected_end_of_file(self, input_string: str, expected_error_position: int) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            with pytest.raises(SpspSyntaxError) as syntax_error:
                list(tokenizer)

            # Assert
            assert syntax_error.value.position == expected_error_position

    @pytest.mark.parametrize(
        'input_string, expected_error_position',
        [
            (r'"abc\ ', 4),
            ("'\\' abc 123 \" \\ ", 14),
        ]
    )
    def test_unescaped_backslash(self, input_string: str, expected_error_position: int) -> None:
        with io.StringIO(input_string) as input_stream:
            # Arrange
            tokenizer = Tokenizer(input_stream)

            # Act
            with pytest.raises(SpspSyntaxError) as syntax_error:
                list(tokenizer)

            # Assert
            assert syntax_error.value.position == expected_error_position
