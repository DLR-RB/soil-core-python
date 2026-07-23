from asyncio import DatagramProtocol, DatagramTransport, create_task, get_running_loop
from typing import Awaitable, Callable, Optional, Tuple, override

from .connection import UdpConnection


class UdpSocket(DatagramProtocol):
    """
    A class to establish SOIL connections via UDP.

    UDP has no concept of client or server, so this class handles both cases.
    New incoming connections can be handled via `onConnection()`,
    while new outgoing connections can be started using `connect()`.
    """

    def __init__(
        self,
        localPort: int,
        maximumPayloadLength: int = 65535,
    ) -> None:
        """
        Create a UDP socket.

        :param localPort: The local port where remotes can connect, and from
                          where outgoing connections are initiated.
        :param maximumPayloadLength: The maximum number of bytes in an incoming
                                     UDP frame.
        """
        #: The shared socket for all connections
        self._transport: DatagramTransport | None = None

        #: A map of all established connections
        self._connections: dict[Tuple[str, int], UdpConnection] = {}

        #: The consumer of new incoming connections
        self._connectionListener: Callable[[UdpConnection], Awaitable[None]] | None = None

        #: The maximum size of UDP frames
        self._maximumPayloadLength = maximumPayloadLength

        self._localPort = localPort
        self._closed = False

        self._ready = create_task(self._start())

    async def _start(self) -> None:
        loop = get_running_loop()

        transport, _ = await loop.create_datagram_endpoint(
            lambda: self,
            local_addr=("0.0.0.0", self._localPort),
        )

        self._transport = transport

    # MARK: Connections

    def connect(
        self,
        host: str | tuple[str, int],
        port: Optional[int] = None,
    ) -> UdpConnection:
        """
        Create a connection to a remote.

        :param host: The hostname or address of the remote.
        :param port: The port of the remote.
        :return: A connection to the specified remote.
        """
        if isinstance(host, tuple):
            remote = host
        else:
            if port is None:
                raise ValueError("Port is required")
            remote = (host, port)

        if remote not in self._connections:
            if self._transport is None:
                raise RuntimeError("UDP socket not started")

            self._connections[remote] = UdpConnection(
                self._transport,
                remote,
            )

        return self._connections[remote]

    def onConnection(self, consumer: Callable[[UdpConnection], Awaitable[None]] | None) -> None:
        """
        Register a consumer of incoming connections.

        :param consumer: The new consumer of incoming connections.
        """
        self._connectionListener = consumer

    # MARK: Frame reception

    @override
    def datagram_received(
        self,
        data: bytes,
        addr: tuple[str, int],
    ) -> None:
        """
        Called by asyncio when a UDP frame is received.
        """
        if self._closed:
            return

        connection = self._connections.get(addr)

        if connection is None:
            if self._transport is None:
                return

            connection = UdpConnection(
                self._transport,
                addr,
            )

            self._connections[addr] = connection

            listener = self._connectionListener
            if listener is not None:
                async def work():
                    await listener(connection)
                create_task(work())

        frame = data[: self._maximumPayloadLength]

        create_task(connection.deliver(frame))

    @override
    def error_received(self, exc: Exception) -> None:
        """
        Called by asyncio when a UDP error is received.

        TODO: Handle/log some errors, close after repeated failures.
        """
        pass

    @override
    def connection_lost(self, exc: Optional[Exception]) -> None:
        """
        Called by asyncio when the UDP transport is closed.
        """
        self.close()

    # MARK: AutoCloseable

    def close(self) -> None:
        """
        Close the UDP socket and all connections.
        """
        if self._transport is not None:
            self._transport.close()

        self._didClose()

    def _didClose(self) -> None:
        """
        Close all connections of the client.
        """
        for connection in self._connections.values():
            connection.close()

        self._connections.clear()
        self._connectionListener = None
        self._closed = True
