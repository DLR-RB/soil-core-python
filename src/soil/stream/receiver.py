from abc import ABC, abstractmethod

from ..requests import Request


class StreamReceiver(ABC):
    """
    A type that can receive bytes from a binary stream for processing.
    """

    @abstractmethod
    def acceptBytes(self, bytes: bytes | bytearray) -> Request:
        """
        Process received bytes from the stream.

        Each call to this method may contain an arbitrary number of bytes.

        Args:
            bytes: The received bytes to process.

        Returns:
            A request representing processing of the received bytes. The
            caller may choose to ignore or await this request.
        """
        raise NotImplementedError
