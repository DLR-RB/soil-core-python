from .path import Path
from .type import ValueType


class Value:

    def __init__(self, value: int | str | float | bytes | Path | None) -> None:
        self.value: int | str | float | bytes | Path | None = value

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
            case bytearray(): return ValueType.DATA
            case memoryview(): return ValueType.DATA

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

    def __str__(self) -> str:
        match self.value:
            case int(n): return str(n)
            case float(n): return formatFloat(n)
            case str(s): return f"'{s}'"
            case Path(p): return str(p)
            case None: return 'null'
            case bytes(b): return b.hex() + ' (DATA)'
            case bytearray(b): return b.hex() + ' (DATA)'
            case _: return f"{self.value} (Unknown)"

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Value):
            return False
        return self.value == value.value

def formatFloat(x: float) -> str:
    s = f"{x:.16f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    return s