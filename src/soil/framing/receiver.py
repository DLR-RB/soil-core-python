from abc import ABC, abstractmethod

from ..requests import Request


class FrameReceiver(ABC):
    """
    A type that can receive frames.

    This interface defines a receiver that can process frames asynchronously.
    """

    @abstractmethod
    def acceptFrame(self, frame: bytes) -> Request:
        """
        Process a received message.

        Each call to this function contains exactly the bytes of one encoded message.

        Parameters:
            frame (bytes):
                The encoded message to process

        Returns:
            Request:
                An awaitable representing the asynchronous processing of the message
        """
