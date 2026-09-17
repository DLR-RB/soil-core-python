from asyncio import DatagramTransport
from typing import Callable, override

from ...framing import FrameConnection, FrameReceiver
from ...utils import Actor, synchronized, queuedAsync


class UdpConnection(Actor, FrameConnection):
    """
    A connection to a remote via UDP.

    UDP does not really have connections, but this class represents a data
    exchange with a remote endpoint.
    There is no support for multiple parallel connections to a single remote
    address.
    """

    def __init__(
        self,
        transport: DatagramTransport,
        remote: tuple[str, int],
    ) -> None:
        """
        Create a UDP connection.

        This function is called by UdpSocket instances.

        :param transport: The shared datagram transport.
        :param remote: The address of the remote.
        """
        super().__init__()
        
        #: The shared datagram transport, provided by a UdpSocket instance
        self._transport = transport

        #: The address of the remote
        self._remote = remote

        #: The receiver of frames coming in over this connection
        self._receiver: FrameReceiver | None = None

        #: The callback to execute when the connection is closed
        self._closeCallback: Callable[[], None] | None = None

        """
        Indicate if the connection was closed (manually,
        or by the UDP socket class that created the connection).

        We don't just check for socket.isClosed(), because other connections
        can remain open even if one connection has been closed manually.
        """
        self._open = True

        self._pending_frames: list[bytes] = []

    # MARK: UDP data flow

    async def deliver(self, frame: bytes) -> None:
        """
        Internal function called by the UdpSocket instance that created the
        connection, when a new frame is received for the connection.

        :param frame: The received frame.
        """
        if self._receiver is None:
            self._pending_frames.append(frame)
            return

        await self._receiver.acceptFrame(frame)

    # MARK: FrameConnection

    @override
    @synchronized
    async def send(self, message: bytes) -> None:
        """
        Send a frame over UDP.

        :param message: The message to send.
        """
        if not self._open:
            return

        try:
            self._transport.sendto(message, self._remote)
        except Exception:
            if self._transport.is_closing():
                self.close()

    # MARK: FrameDistributor

    @override
    @synchronized
    async def setReceiver(self, receiver: FrameReceiver | None) -> None:
        self._receiver = receiver

        if receiver is not None and self._pending_frames:
            for frame in self._pending_frames:
                await receiver.acceptFrame(frame)
            self._pending_frames.clear()

    @override
    @queuedAsync
    def getReceiver(self) -> FrameReceiver | None:
        return self._receiver

    # MARK: Connection

    @override
    async def isOpen(self) -> bool:
        return self._open and not self._transport.is_closing()

    @override
    @synchronized
    async def onClose(self, perform: Callable[[], None] | None) -> None:
        self._closeCallback = perform

    @override
    @synchronized
    async def close(self) -> None:
        if not self._open:
            return

        self._open = False

        if self._closeCallback is not None:
            self._closeCallback()

        await self.shutdown()
        # TODO: Notify UdpSocket that this connection is closed?
