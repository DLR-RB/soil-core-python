from abc import ABC, abstractmethod
from typing import Callable

from ..requests import Request


class Connection(ABC):
    """
    An abstract connection that indicates its status and can be closed
    """

    @abstractmethod
    async def isOpen(self) -> bool:
        """
        Indicate whether the connection is open and can receive and
        transmit data.

        Returns:
            True if the connection is open, otherwise False.
        """
        pass

    @abstractmethod
    def close(self) -> Request:
        """
        Close the connection.

        Returns:
            A request that can optionally be awaited to wait for the
            connection to fully close.
        """
        pass

    @abstractmethod
    async def onClose(self, perform: Callable[[], None] | None) -> None:
        """
        Register a callback to execute when the connection is closed.

        Args:
            block: The callback to execute upon closure.
        """
        pass
