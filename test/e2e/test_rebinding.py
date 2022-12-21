import io

import pytest

from spsp.errors import SpspEvaluationError, SpspInvalidBindingTargetError
from spsp.evaluation import evaluate
from spsp.parser import parse
from spsp.scope import Scope
from spsp.tokenizer import Tokenizer


# noinspection DuplicatedCode
class TestRebind:
    def test_rebind_varargs(self) -> None:
        # Arrange
        code_let = '(let [x y z t *rest-1 *rest-2] [1 2 3 4 5 6])'
        code_rebind = '(rebind [x [y z & *rest-2] t & *rest-1] [1 [2 3 4 5] 6 7 8])'
        with io.StringIO(code_let) as input_stream_let, io.StringIO(code_rebind) as input_stream_rebind:
            let_expressions = list(parse(Tokenizer(input_stream_let)))
            rebind_expressions = list(parse(Tokenizer(input_stream_rebind)))
            scope = Scope.empty()

            # Act
            for e in let_expressions:
                evaluate(e, scope)

            local_scope = scope.derive()

            with pytest.raises(SpspEvaluationError) as evaluation_error:
                for e in rebind_expressions:
                    evaluate(e, local_scope)

            # Assert
            assert isinstance(evaluation_error.value.cause, SpspInvalidBindingTargetError)
            assert 'variadic' in evaluation_error.value.cause.why.lower()
