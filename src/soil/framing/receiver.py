from abc import ABC, abstractmethod


class FrameReceiver(ABC):
    """
    A type that can receive frames.

    This interface defines a receiver that can process frames asynchronously.
    """

    @abstractmethod
    async def didReceive(self, frame: bytes) -> None:
        """
        Process a received message.

        Each call to this function contains exactly the bytes of one encoded message.

        Parameters:
            frame (bytes):
                The encoded message to process

        Returns:
            Awaitable[None]:
                An awaitable representing the asynchronous processing of the message
        """
        pass