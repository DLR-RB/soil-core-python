from asyncio import Queue, Task, create_task, get_running_loop, sleep, CancelledError
from collections.abc import Callable
from typing import Awaitable, override

from soil.messaging import Message, MessageConnection, MessageReceiver
from soil.logging import Logger, NoLogger
from soil.requests import Request, CompletedRequest


class ReconnectingConnection(MessageConnection):
    """
    A wrapper that attempts to keep a connection open,
    by running a reconnect action when the connection is closed
    """
    # TODO: Implement timeout of queued data

    def __init__(self,
        connect: Callable[[], Awaitable[MessageConnection | None]],
        retryInterval: float = 5.0,
        logger: Logger | None = None
    ) -> None:
        self.connect = connect
        self.log = logger or NoLogger()

        self._receiver: MessageReceiver | None = None

        self._connection: MessageConnection | None = None
        # TODO: Increase sleep interval after multiple connection failures
        self._connectionRetryInterval: float = retryInterval

        self._transmissionQueue: Queue[Message] = Queue()
        """ The queue that holds data before being sent """

        self._connectionTask: Task[None] | None = None
        """ The task that keeps the connection alive and reconnects if needed """

        self._transmissionTask: Task[None] | None = None
        """ The task that transmits messages when the connection is available """

        self.loop = get_running_loop()

        self._onClose: Callable[[], None] | None = None
        """ The callback handler, executed only when the reconnection is stopped,
            not when the wrapped connection is closed """

        self._isStarted = False

    def start(self) -> None:
        if self._isStarted:
            return
        self._isStarted = True
        if self._transmissionTask is None:
            self._transmissionTask = create_task(self._transmitQueuedMessages())
        if self._connectionTask is None:
            self._connectionTask = create_task(self._keepConnected())

    def stop(self):
        if not self._isStarted:
            return
        self._isStarted = False
        if self._transmissionTask is not None:
            self._transmissionTask.cancel()
            self._transmissionTask = None
        if self._connectionTask is not None:
            self._connectionTask.cancel()
            self._connectionTask = None
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if self._onClose is not None:
            self._onClose()

    # MARK: MessageConnection

    @override
    def send(self, message: Message) -> Request:
        self.loop.call_soon_threadsafe(self._transmissionQueue.put_nowait, message)
        return CompletedRequest()

    # MARK: MessageDistributor

    @override
    def setReceiver(self, receiver: MessageReceiver | None) -> Request:
        self._receiver = receiver
        if self._connection is not None:
            return self._connection.setReceiver(receiver)
        return CompletedRequest()

    @override
    async def getReceiver(self) -> MessageReceiver | None:
        return self._receiver

    # MARK: Connection

    @override
    async def isOpen(self) -> bool:
        if self._connection is None:
            return False
        return await self._connection.isOpen()

    @override
    def close(self) -> Request:
        self.stop()
        return CompletedRequest()

    @override
    def onClose(self, perform: Callable[[], None] | None) -> Request:
        self._onClose = perform
        return CompletedRequest()


    # MARK: Reconnection

    async def _keepConnected(self) -> None:
        while True:
            if self._connection is not None and await self._connection.isOpen():
                await sleep(self._connectionRetryInterval)
                continue
            # Connection is closed
            if self._connection is not None:
                await self._connection.close()
                self._connection = None
            try:
                self._connection = await self.connect()
            except CancelledError:
                raise
            except Exception:
                await sleep(self._connectionRetryInterval)
                continue
            if self._connection is not None:
                await self._connection.setReceiver(self._receiver)

    # MARK: Transmission

    async def _transmitQueuedMessages(self) -> None:
        while True:
            if self._connection is None or not await self._connection.isOpen():
                await sleep(self._connectionRetryInterval)
                continue
            message = await self._transmissionQueue.get()
            try:
                await self._connection.send(message)
            finally:
                self._transmissionQueue.task_done()
