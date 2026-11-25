import random
from asyncio import (
    CancelledError,
    Queue,
    StreamReader,
    StreamWriter,
    Task,
    create_task,
    current_task,
    wait_for,
)
from collections.abc import Callable
from contextlib import suppress
from typing import override

from ...logging import Logger, NoLogger
from ...stream import StreamConnection, StreamReceiver
from ...utils import Actor, ActorClosedError, queuedAsync, synchronized


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

        #: A unique identifier to identify the connection
        self.uniqueId: int = random.getrandbits(64)

        Actor.__init__(self)

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

        self._dispatchQueue: Queue[bytes] = Queue()
        self._readTask: Task[None] = create_task(self._startReading(), name=f"tcp-read-{self.uniqueId}")
        self._dispatchTask: Task[None] = create_task(self._startDispatching(), name=f"tcp-dispatch-{self.uniqueId}")

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

    async def _closeImmediately(self, reason: str) -> None:
        """
        Close the connection without going through the actor queue.

        The queue may be blocked by a send stuck in drain() (e.g. when the
        remote died without a clean close). The EOF path must not wait
        behind such a send: close the socket directly and run the onClose
        callback.
        """
        self._running = False
        try:
            self._writer.transport.abort()
        except Exception as exc:
            self.log.warning(f"Failed to abort socket after {reason}: {exc}")
        with suppress(Exception):
            self._dispatchTask.cancel()
        perform = self._onClose
        self._onClose = None
        if perform is not None:
            try:
                perform()
            except Exception as exc:
                self.log.error(f"onClose callback failed after {reason}: {exc}")
        with suppress(Exception):
            await self.shutdown()


    async def _gracefulCloseOrEscalate(self, reason: str) -> None:
        """
        Try the regular graceful close(), but do not wait forever behind
        a blocked actor queue (e.g. a send stuck in drain() because the
        remote died). On timeout, abort the socket directly and run the
        onClose callback so the lost connection is detected.
        """
        try:
            await wait_for(self.close().wait(), timeout=2.0)
        except TimeoutError:
            self.log.warning(f"Graceful close timed out ({reason}), aborting")
            await self._closeImmediately(reason)
        except ActorClosedError:
            pass

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
                await self._gracefulCloseOrEscalate("read error")
                return
            if not data:
                # EOF: the remote side closed the connection
                await self._gracefulCloseOrEscalate("EOF")
                return
            self._receivedByteCount += len(data)

            await self._dispatchQueue.put(data)

    async def _startDispatching(self) -> None:
        while True:
            data = await self._dispatchQueue.get()
            if self._receiver is None:
                continue
            try:
                await self._receiver.acceptBytes(data)
            except Exception as e:
                self.log.error(f"Failed to process received data: {e}")
                await self._gracefulCloseOrEscalate("receive dispatch error")
                return

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
        if not self._running or self._writer.is_closing():
            if perform is not None:
                try:
                    perform()
                except Exception as exc:
                    self.log.error(f"onClose callback failed (already closed): {exc}")
            return
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

        if not self._dispatchTask.done():
            self._dispatchTask.cancel()
            with suppress(CancelledError):
                await self._dispatchTask

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if isinstance(other, TcpSocketConnection):
            return other.uniqueId == self.uniqueId
        return False

    def __hash__(self) -> int:
        return hash(self.uniqueId)
