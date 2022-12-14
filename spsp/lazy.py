from dataclasses import dataclass
from typing import Any, Callable

__all__ = [
    'Lazy'
]

NOT_EVALUATED = object()


@dataclass(repr=False)
class Lazy:
    _eval: Callable[[], Any]
    _value: Any = NOT_EVALUATED

    @property
    def value(self) -> Any:
        if self._value is not NOT_EVALUATED:
            return self._value

        self._value = self._eval()
        if isinstance(self._value, Lazy):
            return self._value.value
        return self._value
