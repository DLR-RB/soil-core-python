from abc import ABC, abstractmethod

from .message import Message


class MessageEncoding(ABC):
    """
    An interface to convert messages for the transport layer.

    There may be encodings of messages to only support
    a reduced feature set, such as only encoding a single sample,
    or a single path. In this case, a separate component should
    be inserted into the connection that can split and recombine the
    messages as needed. An example would be `DataMessageSplitter` in `soil.connection`.
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
