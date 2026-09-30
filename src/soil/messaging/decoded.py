from collections.abc import Callable
from typing import override

from ..framing.connection import FrameConnection
from ..framing.receiver import FrameReceiver
from ..logging import Logger, NoLogger
from ..utils.actor import Actor, queuedAsync, synchronized
from .connection import MessageConnection
from .encoding import MessageEncoding
from .message import Message
from .receiver import MessageReceiver


class DecodedConnection(Actor, MessageConnection, FrameReceiver):
    """
    Apply an encoding to a binary connection to create a message-based connection.
    """

    encoding: MessageEncoding
    """ The encoding to use for the messages """

    connection: FrameConnection
    """ The binary connection over which encoded messages are exchanged """

    _receiver: MessageReceiver | None
    """ The receiver getting decoded messages """

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
        self._receiver: MessageReceiver | None = None
        self._pending_frames: list[bytes] = []
        self.log = logger or NoLogger()

    async def initialize(self) -> None:
        await self.connection.setReceiver(self)

    @classmethod
    async def create(cls, connection: FrameConnection, encoding: MessageEncoding, logger: Logger | None = None) -> 'DecodedConnection':
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
        decoded = DecodedConnection(connection, encoding, logger)
        await decoded.initialize()
        return decoded

    @override
    async def shutdown(self) -> None:
        if isinstance(self.encoding, Actor):
            await self.encoding.shutdown()
        await self.connection.close()
        await Actor.shutdown(self)

    # MARK: Frame Connection

    @override
    @synchronized
    async def acceptFrame(self, frame: bytes) -> None:
        """
        Process binary messages received over the connection.

        Attempts to decode the message contained in the data and forwards it to the message connection.
        """
        if self._receiver is None:
            self._pending_frames.append(frame)
            return

        # Attempt to decode the message from the data
        try:
            message = self.encoding.decode(frame)
        except Exception as e:
            self.log.error(f"Failed to decode frame: {e}")
            return

        # Forward the decoded message to the component connection
        await self._receiver.acceptMessage(message)

    # MARK: Message Connection

    @synchronized
    async def send(self, message: Message) -> None:
        """
        Send a message to the component via the underlying transport layer.
        - Parameter message: The message to send
        - Returns: The transmission request, which can be awaited to wait for transmission.
        - Note: The returned request does not wait for message delivery, only transmission.
        """
        try:
            data = self.encoding.encode(message)
        except Exception as e:
            self.log.error(f"Failed to encode frame: {e}")
            return None
        return await self.connection.send(data)

    # MARK: MessageDistributor

    @override
    @synchronized
    async def setReceiver(self, receiver: MessageReceiver | None) -> None:
        """
        Set the receiver for messages produced by this connection.
        - Parameter receiver: The receiver of the messages coming in over this connection.
        """
        self._receiver = receiver

        if receiver is not None:
            while self._pending_frames:
                frame = self._pending_frames.pop(0)
                try:
                    message = self.encoding.decode(frame)
                except Exception as e:
                    self.log.error(f"Failed to decode frame: {e}")
                    continue
                await receiver.acceptMessage(message)

    @override
    @queuedAsync
    def getReceiver(self) -> MessageReceiver | None:
        return self._receiver

    # MARK: Connection

    @override
    async def isOpen(self) -> bool:
        return await self.connection.isOpen()

    @override
    @synchronized
    async def close(self) -> None:
        await self.shutdown()

    @override
    @synchronized
    async def onClose(self, perform: Callable[[], None] | None):
        await self.connection.onClose(perform)
