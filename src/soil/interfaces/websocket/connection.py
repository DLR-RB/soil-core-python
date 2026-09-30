from asyncio import CancelledError, Task, create_task
from collections.abc import Callable
from typing import override

from websockets import ConnectionClosed, State
from websockets.asyncio.connection import Connection as WsConnection

from soil.framing.receiver import FrameReceiver

from ...framing import FrameConnection
from ...logging import Logger, OptionalLogger
from ...utils import Actor, queuedAsync, synchronized


class WebSocketConnection(Actor, FrameConnection):

    def __init__(self,
        connection: WsConnection,
        receiver: FrameReceiver | None = None,
        logger: Logger | None = None
    ) -> None:
        Actor.__init__(self)

        self._clientConnection: WsConnection | None = connection
        self._receiver: FrameReceiver | None = receiver
        self.log = OptionalLogger(logger)
        self._onClose: Callable[[], None] | None = None
        self._readTask: Task[None] | None = create_task(self._readUntilClosed())

    def getLogger(self) -> Logger | None:
        return self.log.getLogger()

    @override
    @synchronized
    async def send(self, message: bytes) -> None:
        if self._clientConnection is None:
            self.log.info("No connection to send message")
            return
        try:
            await self._clientConnection.send(message)
        except ConnectionClosed:
            self.log.info("Failed to send data, connection closed")
            await self._didClose()
        except CancelledError:
            raise
        except Exception as e:
            self.log.error(f"Failed to send data: {e}")

    async def _readUntilClosed(self) -> None:
        """
        Read frames until the connection is closed.
        """
        if self._clientConnection is None:
            self.log.warning("No connection to read")
            return
        if self._clientConnection.state != State.OPEN:
            self.log.warning(f"Connection is not open for reading: {self._clientConnection.state}")
            return
        self.log.debug("Starting reading from socket")
        try:
            async for message in self._clientConnection:
                await self._processFrame(message)
        except ConnectionClosed:
            self.log.info("Read failed, connection to server closed.")
        except CancelledError:
            raise
        except Exception as e:
            self.log.info(f"Unexpected exception '{type(e)}' during read: {e}")
        finally:
            await self.close()

    async def _processFrame(self, message: bytes | str) -> None:
        if isinstance(message, str):
            # Attempt to fix strings, which might be JSON messages
            try:
                message = message.encode('utf-8')
            except:
                self.log.warning("Received string message that could not be encoded as UTF-8")
                return
        self.log.debug(f"Received message with {len(message)} bytes")
        if self._receiver is None:
            self.log.warning("No receiver for message")
            return
        await self._receiver.acceptFrame(message)

    # MARK: FrameDistributor

    @override
    @synchronized
    async def setReceiver(self, receiver: FrameReceiver | None) -> None:
        self._receiver = receiver

    @override
    @queuedAsync
    def getReceiver(self) -> FrameReceiver | None:
        return self._receiver

    # MARK: Connection

    @override
    @queuedAsync
    def isOpen(self) -> bool:
        if self._clientConnection is None:
            return False
        return self._clientConnection.state == State.OPEN

    @override
    @synchronized
    async def close(self) -> None:
        if self._clientConnection is None:
            return
        self.log.debug("Closing")
        if self._readTask is not None:
            self._readTask.cancel()
            self._readTask = None
        match self._clientConnection.state:
            case State.OPEN | State.CONNECTING:
                await self._clientConnection.close()
            case _:
                pass
        await self._didClose()

    async def _didClose(self):
        self._clientConnection = None
        if self._onClose is not None:
            self._onClose()
            self._onClose = None
        await self.shutdown()
        self.log.info("Closed")

    @override
    @synchronized
    async def onClose(self, perform: Callable[[], None] | None) -> None:
        self._onClose = perform
