from dataclasses import dataclass
from typing import Any, Callable


NOT_EVALUATED = object()


@dataclass
class Lazy:
    _eval: Callable[[], Any]
    _value: Any = NOT_EVALUATED

    @property
    def value(self) -> Any:
        if self._value is not NOT_EVALUATED:
            return self._value

        self._value = self._eval()
        return self._value
