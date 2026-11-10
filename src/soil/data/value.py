from __future__ import annotations

from .convertible import ValueConvertible
from .path import Path
from .type import ValueType

type AnyValue = int | str | float | bytes | Path| list[Value] | dict[str, Value] | None


class Value(ValueConvertible):

    value: AnyValue
    """ The wrapped value """

    def __init__(self, value: AnyValue) -> None:
        self.value = value

    def toValue(self) -> Value:
        """
        Convert the instance to a value
        """
        return self

    @classmethod
    def fromValue(cls, value: Value) -> Value:
        """
        Return the value itself, if it is a Value.

        Raises
        ------
        TypeError
            If the argument is not a Value.
        """
        if not isinstance(value, Value): # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"expected a Value, got {type(value).__name__}")
        return value


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
    def listValue(self) -> list[Value] | None:
        if isinstance(self.value, list) and not isinstance(self.value, Path):
            return self.value
        return None

    @property
    def mapValue(self) -> dict[str, Value] | None:
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


    def __getitem__(self, key: str):
        """
        Access a map entry by string key or a list entry by index.
        Raises KeyError / IndexError like dict / list.
        """
        if isinstance(key, str): # pyright: ignore[reportUnnecessaryIsInstance]
            data_map = self.mapValue
            if data_map is None:
                raise TypeError(f"Value of type {self.type} is not a map")
            return data_map[key]
        if isinstance(key, int):
            data_list = self.listValue
            if data_list is None:
                raise TypeError(f"Value of type {self.type} is not a list")
            return data_list[key]
        raise TypeError(f"Invalid key type: {type(key)!r}")

    def __contains__(self, key: str):
        """"key" in value (map) or value-element in value (list)."""
        if self.mapValue is not None:
            return key in self.mapValue
        if self.listValue is not None:
            return any(element == key for element in self.listValue)
        raise TypeError(f"Value of type {self.type} does not support 'in'")

    def __iter__(self):
        """list: elements. map: keys."""
        if self.listValue is not None:
            return iter(self.listValue)
        if self.mapValue is not None:
            return iter(self.mapValue)
        raise TypeError(f"Value of type {self.type} is not iterable")


def formatFloat(x: float) -> str:
    s = f"{x:.16f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    return s
