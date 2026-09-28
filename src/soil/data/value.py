from __future__ import annotations
from typing import Dict, List

from .path import Path
from .type import ValueType


class Value:

    value: int | str | float | bytes | Path| List[Value] | Dict[str, Value] | None
    """ The wrapped value """

    def __init__(self, value: int | str | float | bytes | Path| List[Value] | Dict[str, Value] | None ) -> None:
        self.value = value

    @staticmethod
    def path(*components: str) -> Value:
        return Value(Path(components))

    @property
    def type(self) -> ValueType:
        match self.value:
            case int(): return ValueType.INTEGER
            case float(): return ValueType.DOUBLE
            case str(): return ValueType.STRING
            case Path(): return ValueType.PATH
            case None: return ValueType.NONE
            case bytes(): return ValueType.DATA
            case list(): return ValueType.LIST
            case dict(): return ValueType.MAP

    @property
    def intValue(self) -> int | None:
        if isinstance(self.value, int):
            return self.value
        return None

    @property
    def stringValue(self) -> str | None:
        if isinstance(self.value, str):
            return self.value
        return None

    @property
    def doubleValue(self) -> float | None:
        if isinstance(self.value, float):
            return self.value
        return None

    @property
    def dataValue(self) -> bytes | None:
        if isinstance(self.value, bytes):
            return self.value
        return None

    @property
    def pathValue(self) -> Path | None:
        if isinstance(self.value, Path):
            return self.value
        return None

    @property
    def isNull(self) -> bool:
        return self.value is None

    @property
    def listValue(self) -> List[Value] | None:
        if isinstance(self.value, list) and not isinstance(self.value, Path):
            return self.value
        return None

    @property
    def mapValue(self) -> Dict[str, Value] | None:
        if isinstance(self.value, dict):
            return self.value
        return None

    def __str__(self) -> str:
        match self.value:
            case int(n): return str(n)
            case float(n): return formatFloat(n)
            case str(s): return f"'{s}'"
            case Path(p): return str(p)
            case None: return 'null'
            case bytes(b): return b.hex() + ' (DATA)'
            case list(l): return ", ".join([str(e) for e in l])
            case dict(d): return ", ".join(f"{k} = {v}" for k,v in d.items())
            case _: return f"{self.value} (Unknown)"

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Value):
            return False
        if value.type != self.type:
            return False
        return self.value == value.value


def formatFloat(x: float) -> str:
    s = f"{x:.16f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    return s
