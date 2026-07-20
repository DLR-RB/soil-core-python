from typing import Callable, Tuple, override

from soil.framing import FrameConnection, FrameReceiver
from soil.requests import Request, CompletedRequest
from soil.utils import Actor, synchronized, queuedAsync


class TestConnection(Actor, FrameConnection, FrameReceiver):
    """
    A test frame connection that forwards transmitted frames directly
    to its peer.
    """

    @classmethod
    async def create(cls) -> Tuple["TestConnection", "TestConnection"]:
        """
        Create a pair of interconnected test connections.
        """
        one = TestConnection()
        two = TestConnection()

        await one.setRemote(two)
        await two.setRemote(one)

        return one, two

    def __init__(self):
        Actor.__init__(self)
        # Receiver of frames delivered by this connection.
        self._receiver: FrameReceiver | None = None

        # Remote endpoint receiving transmitted frames.
        self._remote: FrameReceiver | None = None

        # Statistics.
        self.sentMessages = 0
        self.receivedMessages = 0

    # MARK: Internal

    @queuedAsync
    def setRemote(self, remote: FrameReceiver) -> None:
        """ Set the remote endpoint for this connection. """
        self._remote = remote

    # MARK: FrameConnection

    @override
    @synchronized
    async def send(self, message: bytes) -> None:
        """ Send a frame to the remote endpoint. """
        self.sentMessages += 1
        if self._remote is None:
            return
        await self._remote.acceptFrame(message).wait()

    # MARK: FrameDistributor

    @override
    @synchronized
    async def setReceiver(self, receiver: FrameReceiver | None) -> None:
        """ Set the receiver for incoming frames. """
        self._receiver = receiver

    @override
    @queuedAsync
    def getReceiver(self) -> FrameReceiver | None:
        """ Get the current frame receiver. """
        return self._receiver

    # MARK: FrameReceiver

    @override
    @synchronized
    async def acceptFrame(self, frame: bytes) -> None:
        """ Accept a frame from the remote endpoint. """
        self.receivedMessages += 1

        if self._receiver is not None:
            await self._receiver.acceptFrame(frame).wait()

    # MARK: Utilities

    @queuedAsync
    async def resetCounters(self) -> None:
        """ Reset the transmit and receive counters. """
        self.sentMessages = 0
        self.receivedMessages = 0

    # MARK: Connection

    @override
    async def isOpen(self) -> bool:
        """ Indicate whether the connection is open. """
        return True

    @override
    def close(self) -> Request:
        """
        Close the connection.

        This test implementation is always open, so closing is a
        no-op.
        """
        return CompletedRequest()

    @override
    async def onClose(self, perform: Callable[[], None] | None) -> None:
        """
        Register a callback for connection closure.

        This test implementation never closes.
        """
        pass
