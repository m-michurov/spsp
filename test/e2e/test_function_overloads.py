import io

import pytest

from spsp.evaluation import evaluate
from spsp.parser import parse
from spsp.scope import Scope
from spsp.tokenizer import Tokenizer


# noinspection DuplicatedCode
class TestFunctionOverloading:
    @pytest.mark.parametrize(
        'code',
        (
                '(let f (lambda ([x] (+ x 1))))',
                '(let f (lambda [x] (+ x 1)))'
        )
    )
    def test_single_signature(self, code: str) -> None:
        # Arrange
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()
            scope.let('+', lambda a, b: a + b)

            # Act
            for e in expressions:
                evaluate(e, scope)

            f = scope.value('f')

            # Assert
            assert f(1) == 2

    def test_multiple_signatures(self) -> None:
        # Arrange
        code = '(let f (lambda ' \
               '           ([x] (+ x 1))' \
               '           ([x y] (+ (+ x y) 1))))'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()
            scope.let('+', lambda a, b: a + b)

            # Act
            for e in expressions:
                evaluate(e, scope)

            f = scope.value('f')

            # Assert
            assert f(1) == 2
            assert f(5, 6) == 12

    def test_multiple_signatures_with_varargs(self) -> None:
        # Arrange
        code = '(let f (lambda ' \
               '           ([x] (+ x 1))' \
               '           ([x y] (+ (+ x y) 1))' \
               '           ([x y & *rest] *rest)))'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()
            scope.let('+', lambda a, b: a + b)

            # Act
            for e in expressions:
                evaluate(e, scope)

            f = scope.value('f')

            # Assert
            assert f(1) == 2
            assert f(5, 6) == 12
            assert f(5, 6, 7, 8) == (7, 8)
