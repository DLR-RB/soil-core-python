from typing import Callable, override, TYPE_CHECKING

from ..framing import FrameDistributor, FrameConnection, FrameReceiver, StreamFraming
from ..logging import Logger
from ..utils import Actor, synchronized, queuedAsync

if TYPE_CHECKING:
    from .connection import StreamConnection
from .receiver import StreamReceiver


class DecodedStream(Actor, FrameConnection, FrameDistributor, StreamReceiver):
    """
    Apply framing to a binary stream connection to create a frame
    connection.
    """

    def __init__(
        self,
        wrapping: 'StreamConnection',
        framing: StreamFraming,
        logger: Logger | None = None,
    ):
        """
        Wrap a binary stream with framing.

        Args:
            wrapping: The binary stream to apply framing to.
            framing: The framing implementation used by the stream.
            logger: Optional logger for encoding/decoding errors.
        """
        Actor.__init__(self)

        # The framing applied to the stream.
        self._framing = framing

        # The binary stream over which data is exchanged.
        self._stream = wrapping

        # The receiver of decoded frames.
        self._receiver: FrameReceiver | None = None

        # Optional logger for encoding/decoding errors.
        self._log = logger

    @classmethod
    async def create(
        cls,
        wrapping: 'StreamConnection',
        framing: StreamFraming,
        logger: Logger | None = None,
    ) -> "DecodedStream":
        """
        Construct a framed connection and register it as the receiver of
        the underlying stream.
        """
        self = cls(wrapping, framing, logger)
        await wrapping.setReceiver(self).wait()
        return self

    @override
    async def shutdown(self) -> None:
        """ Stop the actor queues and close the stream """
        if isinstance(self._framing, Actor):
            await self._framing.shutdown()
        await self._stream.close()
        await Actor.shutdown(self)

    # MARK: StreamReceiver

    @override
    @synchronized
    async def acceptBytes(self, bytes: bytes) -> None:
        """
        Process received bytes from the stream.

        Each call may contain an arbitrary number of bytes.

        Args:
            bytes: The received stream bytes.

        Returns:
            A request representing asynchronous processing of the bytes.
        """
        messages = await self._framing.processStreamBytes(bytes)
        if not messages:
            return

        receiver = self._receiver
        if receiver is None:
            return

        for message in messages:
            await receiver.acceptFrame(message)

    # MARK: FrameConnection

    @override
    @synchronized
    async def send(
        self,
        message: bytes,
    ) -> None:
        """
        Send a framed message over the connection.

        Returns:
            A request that can optionally be awaited to wait for
            transmission. Completion indicates only that the message has
            been transmitted by the transport layer, not that it has been
            delivered.
        """
        try:
            framed = await self._framing.encodeForStream(message)
        except Exception as exc:
            if self._log is not None:
                self._log.error(f"Failed to encode for stream: {exc}")
            return

        await self._stream.send(framed)

    # MARK: FrameDistributor

    @override
    @synchronized
    async def setReceiver(
        self,
        receiver: FrameReceiver | None,
    ) -> None:
        """
        Set the receiver for decoded frames.

        Args:
            receiver: The receiver of frames produced by this connection.
        """
        self._receiver = receiver

    @override
    @queuedAsync
    def getReceiver(self) -> FrameReceiver | None:
        """
        Get the current frame receiver.
        """
        return self._receiver

    # MARK: Connection

    @override
    async def isOpen(self) -> bool:
        """
        Indicate whether the underlying stream is open.
        """
        return await self._stream.isOpen()

    @override
    @synchronized
    async def close(self) -> None:
        """
        Close the underlying stream connection.
        """
        await self.shutdown()

    @override
    @synchronized
    async def onClose(self, perform: Callable[[], None] | None) -> None:
        """
        Register a callback to execute when the connection closes.
        """
        await self._stream.onClose(perform)
