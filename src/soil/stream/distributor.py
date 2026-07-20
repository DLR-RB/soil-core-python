from abc import ABC, abstractmethod

from ..requests import Request
from .receiver import StreamReceiver


class StreamDistributor(ABC):
    """
    A stream distributor represents a component that transmits stream
    data without being prompted.
    """

    @abstractmethod
    def setReceiver(
        self,
        receiver: StreamReceiver | None,
    ) -> Request:
        """
        Set the receiver of the stream data.

        Args:
            receiver: The receiver that will accept stream data from this
                distributor, or None to remove the current receiver.

        Returns:
            A request representing the receiver update.
        """
        raise NotImplementedError

    @abstractmethod
    async def getReceiver(self) -> StreamReceiver | None:
        """
        Get the current receiver of the stream data.

        Returns:
            The current stream receiver, or None if no receiver has been
            configured.
        """
        raise NotImplementedError