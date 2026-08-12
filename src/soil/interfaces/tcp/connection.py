from asyncio import create_task, Task, StreamReader, StreamWriter, CancelledError, current_task
import random
from collections.abc import Callable
from contextlib import suppress
from typing import override

from ...logging import Logger, NoLogger
from ...stream import StreamConnection, StreamReceiver
from ...utils import Actor, synchronized, queuedAsync, ActorClosedError


class TcpSocketConnection(Actor, StreamConnection):
    """
    A connection over a TCP socket
    """

    def __init__(
        self,
        reader: StreamReader,
        writer: StreamWriter,
        logger: Logger | None = None,
    ) -> None:
        Actor.__init__(self)

        #: A unique identifier to identify the connection
        self.uniqueId: int = random.getrandbits(64)

        #: The wrapped TCP socket connection
        self._reader = reader
        self._writer = writer

        #: The receiver of incoming bytes
        self._receiver: StreamReceiver | None = None

        #: Internal state to cancel the reading thread
        self._running: bool = True

        #: Counter to track the number of received bytes
        self._receivedByteCount = 0

        #: Counter to track the number of transmitted bytes
        self._transmittedByteCount = 0

        #: The callback to execute when the connection is closed
        self._onClose: Callable[[], None] | None = None

        #: The logger to use for internal errors
        self.log: Logger = logger if logger is not None else NoLogger()

        self._readTask: Task[None] = create_task(self._startReading())

    def setLogger(self, logger: Logger) -> None:
        """
        Set the logger for internal errors (read, write, or close)

        :param logger: The logger to use.
        """
        self.log = logger

    @override
    @synchronized
    async def send(self, bytes: bytes | bytearray) -> None:
        """
        Send bytes to the component via the underlying transport layer.

        :param data: The bytes to send.

        Note: Does not guarantee delivery, only that the bytes are handled.
        """
        if self._writer.is_closing():
            self.log.error(f"Connection not open, can't send {len(bytes)} bytes")
            return

        try:
            self._writer.write(bytes)
            await self._writer.drain()
            self._transmittedByteCount += len(bytes)
        except Exception as exc:
            self.log.error(f"Failed to send data over socket: {exc}")
        #

    @override
    @synchronized
    async def setReceiver(self, receiver: StreamReceiver | None) -> None:
        """
        Set the receiver for encoded data from this connection.

        :param receiver: The receiver of the data coming in over this connection.
        """
        self._receiver = receiver

    @override
    @queuedAsync
    def getReceiver(self) -> StreamReceiver | None:
        """
        Get the current receiver of stream bytes.

        :return: The current receiver.
        """
        return self._receiver

    async def _startReading(self) -> None:
        while self._running:
            try:
                data = await self._reader.read(1024)
            except ActorClosedError:
                return
            except CancelledError:
                break
            except Exception as e:
                self.log.error(f"Failed to read from socket: {e}")
                try:
                    await self.close()
                except ActorClosedError:
                    pass
                return
            if not data:
                break

            if self._receiver is not None:
                self._receivedByteCount += len(data)
                await self._receiver.acceptBytes(data)
            #
        #

    def getReceivedBytes(self) -> int:
        """
        Get the total number of bytes received over the connection.

        :return: The total number of received bytes.
        """
        return self._receivedByteCount

    def getTransmittedBytes(self) -> int:
        """
        Get the total number of bytes transmitted over the connection.

        :return: The total number of transmitted bytes.
        """
        return self._transmittedByteCount

    def resetCounters(self) -> None:
        """
        Reset the byte counts for this connection.
        """
        self._receivedByteCount = 0
        self._transmittedByteCount = 0

    # MARK: Connection

    @override
    @queuedAsync
    def isOpen(self) -> bool:
        """
        Indicate if the socket is connected and listening for data.

        :return: True if the socket is connected and listening.
        """
        return not self._writer.is_closing()

    @override
    @synchronized
    async def onClose(self, perform: Callable[[], None] | None) -> None:
        self._onClose = perform

    @override
    @synchronized
    async def close(self) -> None:
        """
        Close the socket, if it is not closed already.

        The callback provided to onClose() is run after the connection is closed.
        """
        if self._writer.is_closing():
            self._running = False
            await self.shutdown()
            return
        if not self._running:
            return
        self._running = False

        try:
            self._writer.close()
            await self._writer.wait_closed()
        except Exception as exc:
            self.log.warning(f"Failed to close socket: {exc}")

        if self._onClose is not None:
            self._onClose()
            self._onClose = None

        current = current_task()
        if (self._readTask is not current and not self._readTask.done()):
            self._readTask.cancel()
            with suppress(CancelledError):
                await self._readTask
        await self.shutdown()

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if isinstance(other, TcpSocketConnection):
            return other.uniqueId == self.uniqueId
        return False

    def __hash__(self) -> int:
        return hash(self.uniqueId)
