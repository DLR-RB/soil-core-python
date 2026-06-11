from abc import abstractmethod

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .receiver import FrameReceiver
    from ..encoding.encoding import MessageEncoding
    from ..messaging.connection import MessageConnection

from ..requests.request import Request
from ..transport.connection import Connection


class FrameConnection(Connection):
    """
    A connector to a component that transmits and receives encoded messages.

    This interface defines the methods for bidirectional communication
    using encoded byte messages.
    """

    @abstractmethod
    def send(self, message: bytes) -> Request:
        """
        Send a message to the component via the underlying transport layer.

        Parameters:
            message (bytes):
                The message to send

        Returns:
            Awaitable[None]:
                An awaitable representing the transmission request.
                Note: Does not guarantee delivery, only that the message was transmitted.
        """
        pass

    @abstractmethod
    async def setReceiver(self, receiver: 'FrameReceiver') -> None:
        """
        Set the receiver for encoded messages from this connector.

        Parameters:
            receiver (EncodedMessageReceiver):
                The receiver of the encoded messages coming in over this connector
        """
        pass

    async def apply(self, encoding: 'MessageEncoding') -> MessageConnection:
        """
        Convert this connector to a message connection using the provided encoding.

        Note: This is a default implementation placeholder. The actual implementation
        would require MessageEncoding and MessageConnection types to be defined.

        Parameters:
            encoding (MessageEncoding):
                The encoding to use for messages over the connector

        Returns:
            MessageConnection:
                The message-based connection
        """
        from ..messaging.decoded import DecodedConnection
        return await DecodedConnection.create(self, encoding)
