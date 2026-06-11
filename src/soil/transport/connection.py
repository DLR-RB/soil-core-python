from abc import ABC, abstractmethod
from typing import Callable, Optional

from ..requests.request import Request


class Connection(ABC):
    """
    An abstract connection that indicates its status and can be closed
    """

    @abstractmethod
    async def isOpen(self) -> bool:
        """ Indicate if the connection is open and can receive and transmit data """
        pass

    @abstractmethod
    def close(self) -> Request:
        """ Close the connection """
        pass

    @abstractmethod
    async def onClose(self, perform: Optional[Callable[[], None]]) -> None:
        """
        Execute a closure when the connection is closed
        Parameters:
            block ():
                The closure to execute
        """
        pass
