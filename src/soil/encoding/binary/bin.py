from typing import override

from ...messaging import Message, MessageEncoding
from .decode import decodeMessage
from .encode import encodeMessage


class BinaryEncoding(MessageEncoding):

    @override
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
        return encodeMessage(message)


    @override
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
        return decodeMessage(data)
