

from typing import Iterable, List, override


class Path(list[str]):
    """
    A SOIL path (an array of strings) identifying a state, input or output
    """
    def __init__(self, iterable: Iterable[str] | None = None) -> None:
        if iterable is None:
            super().__init__()
        else:
            super().__init__(iterable)

    @staticmethod
    def of(*components: str) -> Path:
        return Path(components)

    @property
    def isEmpty(self) -> bool:
        return len(self) == 0

    def appending(self, suffix: str | List[str] | Path) -> Path:
        if isinstance(suffix, str):
            return Path(self + [suffix])
        elif isinstance(suffix, Path):
            return Path(self + suffix)
        else:
            return Path(self + suffix)

    @override
    def __str__(self) -> str:
        return " > ".join(self)

    def __add__(self, other: Iterable[str]) -> Path: # type: ignore
        if not isinstance(other, list):
            return NotImplemented
        return type(self)(super().__add__(other))

    def __radd__(self, other: Iterable[str]) -> Path:
        if not isinstance(other, list):
            return NotImplemented
        return type(self)(other + list(self))

    def __iadd__(self, other: Iterable[str]) -> Path:
        super().__iadd__(other)
        return self