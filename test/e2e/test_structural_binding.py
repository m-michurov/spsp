import io

import pytest

from spsp import parse, Tokenizer, Scope, evaluate
from spsp.errors import SpspEvaluationError


# noinspection DuplicatedCode
class TestStructuralBindings:
    def test_bind_to_collection(self) -> None:
        # Arrange
        code = '(let [x y z] [1 2 3])'
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

    def test_bind_to_collection_nested(self) -> None:
        # Arrange
        code = '(let [x [y z] t] [1 [2 3] 4])'
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
            assert scope.value('t') == 4

    def test_bind_to_iterator(self) -> None:
        # Arrange
        code = '(let [x y] (map int [1 2]))'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()

            # Act
            with pytest.raises(SpspEvaluationError) as evaluation_error:
                for e in expressions:
                    evaluate(e, scope)

            # Assert
            assert isinstance(evaluation_error.value.cause, TypeError)

    def test_bind_attributes(self) -> None:
        # Arrange
        code = '(let [x::a x::b] [1 2])'
        with io.StringIO(code) as input_stream:
            expressions = list(parse(Tokenizer(input_stream)))
            scope = Scope.empty()

            import types
            scope.let('x', types.SimpleNamespace())

            # Act
            for e in expressions:
                evaluate(e, scope)

            # Assert
            assert scope.value('x').a == 1
            assert scope.value('x').b == 2
