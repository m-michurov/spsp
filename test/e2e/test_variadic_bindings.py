import io

import pytest

from spsp import parse, Tokenizer, Scope, evaluate
from spsp.errors import SpspInvalidBindingError


# noinspection DuplicatedCode
class TestVariadicBindings:
    def test_bind_to_collection(self) -> None:
        # Arrange
        code = '(let [x & *rest] [1 2 3])'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()

            # Act
            for e in expressions:
                evaluate(e, scope)

            # Assert
            assert scope.value('x') == 1
            assert scope.value('*rest') == (2, 3)

    def test_bind_to_collection_empty_varargs(self) -> None:
        # Arrange
        code = '(let [x y z & *rest] [1 2 3])'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()

            # Act
            for e in expressions:
                evaluate(e, scope)

            # Assert
            assert scope.value('x') == 1
            assert scope.value('y') == 2
            assert scope.value('z') == 3
            assert scope.value('*rest') == ()

    def test_bind_to_collection_only_varargs(self) -> None:
        # Arrange
        code = '(let [& *rest] [1 2 3])'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()

            # Act
            for e in expressions:
                evaluate(e, scope)

            # Assert
            assert scope.value('*rest') == (1, 2, 3)

    def test_bind_to_collection_not_enough_values(self) -> None:
        # Arrange
        code = '(let [x y z t & *rest] [1 2 3])'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()

            # Act
            with pytest.raises(SpspInvalidBindingError) as bind_error:
                for e in expressions:
                    evaluate(e, scope)

            # Assert
            assert 'not enough values' in bind_error.value.why.lower()

    def test_bind_to_collection_nested(self) -> None:
        # Arrange
        code = '(let [x [y z & *rest-2] t & *rest-1] [1 [2 3 4 5] 6 7 8])'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()

            # Act
            for e in expressions:
                evaluate(e, scope)

            # Assert
            assert scope.value('x') == 1
            assert scope.value('y') == 2
            assert scope.value('z') == 3
            assert scope.value('t') == 6
            assert scope.value('*rest-2') == (4, 5)
            assert scope.value('*rest-1') == (7, 8)

    def test_bind_to_iterator(self) -> None:
        # Arrange
        code = '(let [x & *rest] (map int [1 2 3]))'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()

            # Act & Assert
            with pytest.raises(TypeError):
                for e in expressions:
                    evaluate(e, scope)

    def test_variadic_macro(self) -> None:
        # Arrange
        code = '((macro [& idents] (expr! (inline-value! (list (map (lambda [it] it::name) idents))))) x y z)'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()

            # Act
            result = None
            for e in expressions:
                result = evaluate(e, scope)

            # Assert
            assert result == ['x', 'y', 'z']

    def test_variadic_function(self) -> None:
        # Arrange
        code = '((lambda [& nums] nums) 1 2 3)'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()

            # Act
            result = None
            for e in expressions:
                result = evaluate(e, scope)

            # Assert
            assert result == (1, 2, 3)
