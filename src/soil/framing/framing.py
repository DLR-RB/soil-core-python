from abc import ABC, abstractmethod
from typing import List


class StreamFraming(ABC):
    """
    A type that provides framing for binary data streams.
    """

    @abstractmethod
    async def encodeForStream(self, message: bytes) -> bytes:
        """
        Add framing information to an encoded message to make it suitable
        for transmission over a binary stream.

        Args:
            message: The message to frame.

        Returns:
            The framed message.

        Raises:
            Exception: If framing information could not be added.
        """
        raise NotImplementedError

    @abstractmethod
    async def processStreamBytes(self, data: bytes) -> List[bytes]:
        """
        Extract frames from binary stream data.

        Args:
            data: Newly received bytes from the binary stream.

        Returns:
            A list of decoded messages that could be extracted from the
            supplied stream data.

        Raises:
            Exception: If frame decoding fails.
        """
        raise NotImplementedError
