from dataclasses import dataclass
from typing import Any

__all__ = [
    'SpspBaseError',
    'SpspSyntaxError',
    'SpspNameError',
    'SpspAttributeError',
    'SpspInvalidBindingError',
    'SpspInvalidKeywordUsageError',
    'SpspTypeError',
    'SpspValueError',
    'SpspArityError',
    'SpspInvalidBindingTargetError'
]


class SpspBaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class SpspSyntaxError(SpspBaseError):
    position: int
    description: str

    def __str__(self) -> str:
        return f'{self.description} at {self.position}'


@dataclass(frozen=True)
class SpspNameError(SpspBaseError):
    name: str


@dataclass(frozen=True)
class SpspAttributeError(SpspBaseError):
    obj: Any
    attribute: str


@dataclass(frozen=True)
class SpspTypeError(SpspBaseError):
    why: str


@dataclass(frozen=True)
class SpspValueError(SpspBaseError):
    why: str


@dataclass(frozen=True)
class SpspInvalidBindingError(SpspBaseError):
    why: str


@dataclass(frozen=True)
class SpspInvalidBindingTargetError(SpspBaseError):
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
    what: Any
    expected: int
    actual: int

    def __str__(self) -> str:
        return f'{self.what}: expected {self.expected} arguments, got {self.actual}'


@dataclass(frozen=True)
class SpspInvalidKeywordUsageError(SpspBaseError):
    pass
