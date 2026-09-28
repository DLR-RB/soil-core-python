
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from .value import Value


class ValueConvertible(ABC):
    """ A type that can be converted to and from a value """

    @classmethod
    @abstractmethod
    def fromValue(cls, value: Value) -> Self | None:
        """
        Create an instance of the type from a value, if possible
        """
        ...

    @abstractmethod
    def toValue(self) -> Value:
        """
        Convert the instance to a value.
        """
        ...
