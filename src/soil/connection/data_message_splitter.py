import random
from typing import Callable, Dict, List, Optional, Tuple, Any, override

from ..data import Path, SampleTree, Timestamp, Value
from ..logging import Logger
from ..messaging import Message, MessageConnection, MessageReceiver, MessageType
from ..requests import Request
from ..utils import Actor, synchronized


class MessageSequence:
    """
    A sequence of messages to transmit that belong to a batch.
    """

    def __init__(self, request: Optional[int]):
        self.request = request

        # List of (path, value, timestamp)
        self.messages: List[Tuple[Any, Any, Any]] = []

        # Number of messages received
        self.received: int = 0

        # Total messages expected
        self.total: int = 0

    def _update(self, count: Optional[int]) -> None:
        """Update the expected message count."""
        if count is not None and count > self.total:
            self.total = count

    def _didReceiveMessage(self) -> None:
        self.received += 1
        if self.received > self.total:
            self.total = self.received

    def add(self, message: Message) -> None:
        """Add the contents of a message."""
        self._update(message.count)
        self._addTree(message.data, message.path)
        self._didReceiveMessage()

    def _addValue(self, path: Path, value: Value, timestamp: Timestamp | None) -> None:
        self.messages.append((path, value, timestamp))

    def _addTree(self, tree: SampleTree, path: Path) -> None:
        for sample in tree.samples:
            self._addValue(path, sample.value, sample.timestamp)

        for name, child in tree.children.items():
            self._addTree(child, path + [name])

    @property
    def isComplete(self) -> bool:
        return self.received == self.total

    def countAndId(self) -> Tuple[int | None, int | None]:
        """
        Compute the outgoing batch count and id.
        """
        if self.request is not None:
            return len(self.messages), self.request

        if len(self.messages) <= 1:
            return None, None

        return len(self.messages), random.randint(0, 0xFFFF)


class DataMessageSplitter(Actor, MessageConnection, MessageReceiver):
    """
    A converter that wraps a connection that sends complex messages and converts them to simple value messages.

    Messages over arbitrary connections may contain multiple samples or additional child data.
    The splitter splits these complex messages into multiple smaller messages only containing a single value,
    to support message encodings that can't handle these fields.

    For trees already split into multiple messages, it waits until all are received,
    and then sets the total count with the same request id for all simple messages.
    """

    def __init__(self, connection: MessageConnection):
        Actor.__init__(self)

        self._connection: MessageConnection = connection
        """ The wrapped connection for which to split the outgoing messages """

        self._receiver: MessageReceiver | None = None
        """ The original receiver of the incoming messages """

        self._log: Logger | None = None
        """ The logger for internal errors """

        self._outgoingMessages: Dict[int, MessageSequence] = {}
        """
        The cached outgoing message batches,
        so that the total number of messages can be calculated
        """

        self.shouldWarnAboutMissingReceiver: bool = True
        """ In internal flag to only once create a log message if no receiver is present """

    @classmethod
    async def create(cls, connection: MessageConnection):
        """
        Async constructor.
        """
        self = cls(connection)
        await connection.setReceiver(self)
        return self

    # MARK: Sending

    @override
    @synchronized
    async def send(self, message: Message) -> None:
        if message.type == MessageType.DATA:
            await self._sendData(message)
        else:
            await self._connection.send(message)

    async def _sendData(self, message: Message):
        sequence = self._createOrGet(message.id)
        sequence.add(message)

        if not sequence.isComplete:
            return

        self._remove(sequence)
        await self._sendSequence(sequence)

    async def _sendSequence(self, sequence: MessageSequence):
        count, batch_id = sequence.countAndId()

        for path, value, timestamp in sequence.messages:
            out = Message.value(
                value=value,
                path=path,
                timestamp=timestamp,
                request=batch_id,
                totalMessages=count,
            )
            await self._connection.send(out)

    def _createOrGet(self, request: Optional[int]) -> MessageSequence:
        if request is None:
            # Sequence is not stored, because it's immediatelly sent
            return MessageSequence(None)

        if request not in self._outgoingMessages:
            self._outgoingMessages[request] = MessageSequence(request)

        return self._outgoingMessages[request]

    def _remove(self, sequence: MessageSequence):
        if sequence.request is not None:
            self._outgoingMessages.pop(sequence.request, None)

    def _removeAll(self):
        self._outgoingMessages.clear()

    # MARK: Receiver management

    @override
    @synchronized
    async def setReceiver(self, receiver: MessageReceiver | None) -> None:
        self._receiver = receiver

    @override
    async def getReceiver(self) -> MessageReceiver | None:
        return self._receiver

    # MARK: Connection API

    @override
    async def isOpen(self):
        return await self._connection.isOpen()

    @override
    @synchronized
    async def close(self) -> None:
        await self._connection.close()
        await self.shutdown()

    @override
    def onClose(self, perform: Optional[Callable[[], None]]) -> Request:
        def wrapped():
            self._removeAll()
            if perform is not None:
                perform()

        return self._connection.onClose(wrapped)

    # MARK: Incoming messages

    @override
    @synchronized
    async def acceptMessage(self, message: Message) -> None:
        if self._receiver is None:
            if self.shouldWarnAboutMissingReceiver:
                if self._log is not None:
                    self._log.warning("No receiver for message")
                self.shouldWarnAboutMissingReceiver = False
            return

        self.shouldWarnAboutMissingReceiver = True

        await self._receiver.acceptMessage(message)
