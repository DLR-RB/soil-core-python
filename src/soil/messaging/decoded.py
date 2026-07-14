from typing import Callable, Optional

from ..encoding.encoding import MessageEncoding
from ..framing.connection import FrameConnection
from ..framing.receiver import FrameReceiver
from ..logging import Logger, NoLogger
from .message import Message
from ..requests.request import Request
from ..utils.actor import Actor, synchronized, queued

from .connection import MessageConnection
from .receiver import MessageReceiver


class DecodedConnection(Actor, MessageConnection, FrameReceiver):
    """
    Apply an encoding to a binary connection to create a message-based connection.
    """

    """ The encoding to use for the messages """
    encoding: MessageEncoding

    """ The binary connection over which encoded messages are exchanged """
    connection: FrameConnection

    """ The receiver getting decoded messages """
    receiver: MessageReceiver | None

    def __init__(self, connection: FrameConnection, encoding: MessageEncoding, logger: Logger | None = None):
        """
        Wrap a binary connection with an encoding.
        Parameters:
            connection (FrameConnection):
                The binary connection to apply the encoding to
            encoding (MessageEncoding):
                The encoding used for the binary connection.

        Note:
            If you use the constructor directly, then you must call `initialize()` on the new object.
            Alternatively, use `DecodedConnection.create()`
        """
        Actor.__init__(self)
        self.connection = connection
        self.encoding = encoding
        self.receiver: MessageReceiver | None = None
        self.logger = logger or NoLogger()

    async def initialize(self) -> None:
        await self.connection.setReceiver(self)

    @classmethod
    async def create(cls, connection: FrameConnection, encoding: MessageEncoding) -> 'DecodedConnection':
        """
        Wrap a binary connection with an encoding.
        Parameters:
            connection (FrameConnection):
                The binary connection to apply the encoding to
            encoding (MessageEncoding):
                The encoding used for the binary connection.
        Returns:
            DecodedConnection:
                The connection decoded using the provided encoding
        """
        decoded = DecodedConnection(connection, encoding)
        await decoded.initialize()
        return decoded

    # MARK: Frame Connection

    async def didReceive(self, frame: bytes) -> None:
        """
        Process binary messages received over the connection.

        Attempts to decode the message contained in the data and forwards it to the message connection.
        """
        await self._didReceive(frame)

    @queued(default=None)
    async def _didReceive(self, frame: bytes) -> None:
        if self.receiver is None:
            self.logger.warning("No receiver for frame")
            return

        # Attempt to decode the message from the data
        try:
            message = self.encoding.decode(frame)
        except Exception as e:
            self.logger.error(f"Failed to decode frame: {e}")
            return

        # Forward the decoded message to the component connection
        await self.receiver.didReceive(message)

    # MARK: Message Connection

    def send(self, message: Message) -> Request:
        """
        Send a message to the component via the underlying transport layer.
        - Parameter message: The message to send
        - Returns: The transmission request, which can be awaited to wait for transmission.
        - Note: The returned request does not wait for message delivery, only transmission.
        """
        return self._send(message)

    @synchronized
    async def _send(self, message: Message) -> None:
        """
        Send a message (actor-isolated) over the connection.

        Attempts to encode the message using the encoding layer, and forwards it over the data connection.
        - Parameter message: The message to transmit
        """
        try:
            data = self.encoding.encode(message)
        except Exception as e:
            self.logger.error(f"Failed to encode frame: {e}")
            return None
        return await self.connection.send(data)

    async def setReceiver(self, receiver: MessageReceiver) -> None:
        """
        Set the receiver for messages produced by this connection.
        - Parameter receiver: The receiver of the messages coming in over this connection.
        """
        self.receiver = receiver

    # MARK: Connection

    async def isOpen(self) -> bool:
        return await self.connection.isOpen()

    def close(self) -> Request:
        return self.connection.close()

    async def onClose(self, perform: Optional[Callable[[], None]]):
        await self.connection.onClose(perform)
