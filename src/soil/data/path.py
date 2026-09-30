

from collections.abc import Iterable
from typing import Self, override


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
    def of(*components: str) -> 'Path':
        return Path(components)

    @property
    def isEmpty(self) -> bool:
        return len(self) == 0

    @property
    def size(self) -> int:
        return len(self)

    def appending(self, suffix: 'str | list[str] | Path') -> 'Path':
        if isinstance(suffix, str):
            return Path(self + [suffix])
        elif isinstance(suffix, Path):
            return Path(self + suffix)
        else:
            return Path(self + suffix)

    def hasPrefix(self, prefix: 'Path') -> bool:
        """
        Check if the path starts with another path.
        - Parameter prefix: The path to check as the prefix
        - Returns: `true`, if this path starts with the prefix path
        """
        # A prefix can only match if the path is at least as the prefix
        if self.size < prefix.size:
            return False
        for index in range(prefix.size):
            if self[index] != prefix[index]:
                return False
        return True

    def removingPrefix(self, prefix: 'Path') -> 'Path':
        """
        Remove a prefix from the path.
        - Note: If the path does not start with the prefix, then it remains unchanged.
        - Parameter prefix: The path to remove as the prefix
        - Returns: The path without the given prefix.
        """
        if not self.hasPrefix(prefix):
            return self
        return Path(self[prefix.size:])

    def commonPrefix(self, other: 'Path') -> 'Path':
        """
        Determine the maximum prefix that the path shares with another path
        - Parameter other: The second path to determine the common prefix
        - Returns: The prefix matching both paths
        """
        maxIndex = min(other.size, self.size)
        common: list[str] = []
        for index in range(maxIndex):
            if self[index] != other[index]:
                break
            common.append(self[index])
        return Path(common)

    def extractCommonPrefix(self, other: 'Path') -> tuple['Path', 'Path', 'Path']:
        """
        Compute the prefix of the path in common with a given path,
        and return the remaining relative paths.
        - Parameter other: The second path to determine the common prefix
        - Returns: The prefix matching both paths, and the remaining subpaths
        """
        prefix = self.commonPrefix(other)
        remainder = Path(self[prefix.size:])
        otherRemainder = Path(other[prefix.size:])
        return (prefix, remainder, otherRemainder)

    def __lt__(self, value: list[str]) -> bool:
        """
        Sort paths by comparing their components.

        Paths are sorted by their components starting from the beginning of the path,
        and shorter paths are sorted before longer paths.

        ```
        ["a", "b"] < ["b"] // true
        ["a", "b"] < ["a", "c"] // true
        ["a", "b"] < ["a", "b", "c"] // true
        ```
        """
        minCount = min(self.size, len(value))
        for i in range(minCount):
            if self[i] < value[i]:
                return True
            if self[i] > value[i]:
                return False
        return self.size < len(value)

    @override
    def __str__(self) -> str:
        return " > ".join(self)

    def __add__(self, other: Iterable[str]) -> 'Path': # type: ignore
        if not isinstance(other, list):
            return NotImplemented
        return type(self)(super().__add__(other))

    def __radd__(self, other: Iterable[str]) -> 'Path':
        if not isinstance(other, list):
            return NotImplemented
        return type(self)(other + list(self))

    def __iadd__(self, other: Iterable[str]) -> Self:
        super().__iadd__(other)
        return self
