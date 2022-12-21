from dataclasses import dataclass
from typing import Any

__all__ = [
    'SpspBaseError',
    'SpspSyntaxError',
    'SpspNameError',
    'SpspInvalidBindingError',
    'SpspInvalidKeywordUsageError',
    'SpspValueError',
    'SpspArityError',
    'SpspInvalidBindingTargetError',
    'SpspEvaluationError'
]


class SpspBaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class SpspSyntaxError(SpspBaseError):
    """
    Generic syntax error.

    This is a parse time error.
    """
    position: int
    description: str

    def __str__(self) -> str:
        return f'{self.description} at {self.position}'


@dataclass(frozen=True)
class SpspNameError(SpspBaseError):
    """
    This error is used to indicate that a given name could not be resolved in current scope.

    This is an evaluation time error.
    """
    name: str


@dataclass(frozen=True)
class SpspValueError(SpspBaseError):
    """
    This error is used to indicate that a value is not what it was expected to be.

    For example, `SpspValueError` is raised by special form `lambda` when its arguments list is not a list expression.

    This is an evaluation time error.
    """
    why: str


@dataclass(frozen=True)
class SpspInvalidBindingError(SpspBaseError):
    """
    This error is used to indicate that a binding operation cannot be performed.

    This is an evaluation time error.
    """
    why: str


@dataclass(frozen=True)
class SpspInvalidBindingTargetError(SpspBaseError):
    """
    This error is used to indicate that binding-related operation cannot be performed for a given target.

    This is an evaluation time error.
    """
    target: str | Any
    why: str | None = None

    def __str__(self) -> str:
        prefix = self.why or 'Cannot bind to'
        if not prefix.endswith(' '):
            prefix += ' '

        if isinstance(self.target, str):
            return prefix + f'"{self.target}"'

        return prefix + str(type(self.target))


@dataclass(frozen=True)
class SpspArityError(SpspBaseError):
    """
    This error is used to indicate that a built-in special form is used with wrong number of arguments.

    This is an evaluation time error.
    """
    what: Any
    expected: int | None = None
    actual: int | None = None

    def __str__(self) -> str:
        if self.expected is not None and self.actual is not None:
            return f'{self.what}: expected {self.expected} arguments, got {self.actual}'

        if self.expected is not None:
            return f'{self.what}: expected {self.expected} arguments'

        if self.actual is not None:
            return f'{self.what}: got {self.actual} arguments'

        return self.what


@dataclass(frozen=True)
class SpspInvalidKeywordUsageError(SpspBaseError):
    pass


@dataclass(frozen=True)
class SpspEvaluationError(SpspBaseError):
    cause: Exception
    position: int
