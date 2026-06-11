from abc import ABC, abstractmethod

from ..messaging.message import Message


class MessageEncoding(ABC):
    """
    An interface to convert messages for the transport layer.
    """

    @abstractmethod
    def encode(self, message: Message) -> bytes:
        """
        Convert a message to binary data for transmission.

        Parameters:
            message (Message):
                The message to encode

        Returns:
            (bytes)
                The binary data of the encoded message
        """
        pass

    @abstractmethod
    def decode(self, data: bytes) -> Message:
        """
        Extract a message from binary data.

        Parameters:
            data(bytes)
                The encoded message

        Returns:
            Message
                The decoded message
        """
        pass
