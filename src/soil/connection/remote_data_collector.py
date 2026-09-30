from asyncio import CancelledError, Task, create_task, sleep
from typing import override

from ..components import Distributor, Receiver
from ..data import Path, SampleTree
from ..messaging import Message, MessageReceiver, MessageType
from ..requests import CompletedRequest, Request
from .received_tree import IncompleteReceivedTree


class RemoteDataCollector(Distributor, MessageReceiver):
    """
    Combine messages with ids into trees.
    """

    def __init__(
        self,
        receiver: Receiver | None,
        batchTimeout: float,
    ):
        """
        Create a handler to manage messages.
        """

        #: The timeout in seconds until a batch times out
        self._batchTimeout = batchTimeout

        #: The receiver ingesting updates from the remote component
        self._receiver = receiver

        #: The currently tracked batches, indexed by their id
        self._activeBatches: dict[int, IncompleteReceivedTree] = {}

    def _startBatchTimeout(self, id: int) -> Task[None]:
        """
        Create a task that times out after a while.

        Args:
            id: The id of the batch that timed out.

        Note:
            ``cancel()`` is called with the provided id when the task reaches
            its timeout.
        """

        async def timeout():
            try:
                await sleep(self._batchTimeout)
                await self.cancelBatch(id)
            except CancelledError:
                pass

        return create_task(timeout())

    async def cancelBatch(self, id: int) -> bool:
        """
        Cancel an incomplete batch.

        Args:
            id: The id of the batch to cancel.

        Returns:
            ``True`` if the batch was found and canceled.
        """
        batch = self._activeBatches.get(id)
        if batch is None:
            # No active batch, so we ignore the timeout
            return False

        # Note: The batch is removed once `_didComplete()` is called by the
        # batch.
        batch.finish()
        return True

    def _didComplete(
        self,
        id: int,
        tree: SampleTree,
        path: Path,
    ):
        """
        Function called by each batch when it finishes.
        """
        self._activeBatches.pop(id, None)

        if self._receiver is not None:
            create_task(self._receiver.accept(tree, path).wait())

    @property
    def numberOfIncompleteBatches(self) -> int:
        """
        The number of currently active batches.
        """
        return len(self._activeBatches)

    def hasIncompleteBatch(self, id: int) -> bool:
        """
        Indicate if a message batch with the given id is currently being
        received.

        Args:
            id: The id of the batch.

        Returns:
            ``True`` if a batch with the id is in progress.
        """
        return id in self._activeBatches

    # MARK: - Distributor

    @override
    def setReceiver(self, receiver: Receiver | None) -> Request:
        """
        Set the receiver for data received over the connection.

        Args:
            receiver: The receiver of the data coming in over this connection.
        """
        self._receiver = receiver
        return CompletedRequest()

    @override
    async def getReceiver(self) -> Receiver | None:
        """
        Get the receiver of incoming messages of this connection.
        """
        return self._receiver

    # MARK: - Message Receiver

    @override
    def acceptMessage(self, message: Message) -> Request:
        """
        Process a received data message, which may update an existing batch, or
        create a new one.

        Args:
            message: The received data message.
        """
        self._didReceive(message)
        return CompletedRequest()

    def _didReceive(self, message: Message) -> None:
        if message.type != MessageType.DATA:
            # Not a data message, so we ignore it
            return

        if message.id is None:
            # No batch id, so we just forward the message data
            if self._receiver is not None:
                create_task(
                    self._receiver.accept(message.data, message.path).wait()
                )
            return

        batch = self._getOrCreateBatch(message.id)
        batch.update(message)

        if batch.hasReceivedAllExpectedMessages:
            batch.finish()

    def _getOrCreateBatch(self, id: int) -> IncompleteReceivedTree:
        """
        Select or create a batch for an id.
        """
        batch = self._activeBatches.get(id)
        if batch is not None:
            return batch

        # No active batch, so we need to create a new one
        timeoutTask = self._startBatchTimeout(id)

        batch = IncompleteReceivedTree(
            timeout=timeoutTask,
            onComplete=lambda tree, path: self._didComplete(
                id,
                tree,
                path,
            ),
        )

        self._activeBatches[id] = batch
        return batch
