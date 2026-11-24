from collections.abc import Callable
from typing import override

from ..components import Connection, Storage
from ..data import Path, SampleTree, Timestamp
from ..messaging import Message, MessageConnection, MessageReceiver, MessageType
from ..requests import Request
from ..utils import Actor, synchronized


class HostedStorage(Actor, Storage, MessageReceiver, Connection):
    """
    Expose a storage over a transport interface.

    The class can be used to provide access to a storage interface via a remote
    connection. Request messages received over the connection are processed,
    and the requested data is returned. Data received over the connection is
    inserted into the provided storage. Deletion requests are also executed.
    """

    def __init__(self, storage: Storage, connection: MessageConnection):
        Actor.__init__(self)
        self._storage = storage
        """ The storage that is exposed over the connection """

        self.connection = connection
        """ The connection over which the storage is hosted """

    @classmethod
    async def create(
        cls,
        storage: Storage,
        connection: MessageConnection,
    ) -> 'HostedStorage':
        """
        Create a hosted storage.

        Args:
            storage: The storage to expose.
            connection: The connection over which the storage should be
                accessible.
        """
        self = cls(storage, connection)

        # Register to receive messages from the component
        await connection.setReceiver(self)

        return self

    def _send(self, message: Message) -> Request:
        """
        Send a message to the component.

        Args:
            message: The message to send.

        Note:
            If no message callback is available, then the message is discarded.

        Returns:
            The request to send the message.
        """
        return self.connection.send(message)

    # MARK: - Response Handling

    async def _didReceiveData(self, message: Message) -> None:
        """
        Process a data message, by checking which request it matches.

        Args:
            message: The received data message.
        """
        # Note: We know that the message is a data message

        # Schedule the insert
        request = self._storage.accept(message.data, message.path)

        # Check if the request expects a response
        if message.id is None:
            return

        # Wait for the insert to complete and send an acknowledgement
        # TODO: Dispatch to the background to not block other requests from
        # being processed?
        await request

        self._send(Message.acknowledge(message.id, message.path))

    async def _didReceiveRequest(self, message: Message) -> None:
        """
        Processing point for all data requests.

        Args:
            message: The data request.
        """
        # TODO: Schedule this on another thread to not block other requests in
        # the meantime?
        tree = await self._storage.tree(
            message.path,
            message.time,
            message.end,
            message.depth,
            message.count,
        )

        if message.id is None:
            self._sendTree(tree, message.path, None, None)
            return

        count = tree.numberOfNodesWithSamples

        if count == 0:
            # Send at least one message if a request id is present
            self._send(
                Message.samples(
                    samples = [],
                    path = message.path,
                    request = message.id,
                    totalMessages = 1,
                )
            )
            return

        self._sendTree(tree, message.path, message.id, count)

    def _sendTree(
        self,
        tree: SampleTree,
        path: Path,
        request: int | None,
        count: int | None,
    ) -> None:
        """
        Send the contents of a tree as individual data messages per node.

        Args:
            tree: The tree to send.
            path: The path of the tree root in the data model.
            request: The id to include in the response.
            count: The total number of messages to be indicated in each
                message.
        """
        if tree.samples:
            # TODO: Should we send an empty message for existing tree nodes
            # without a value?
            # If we change this, then the `count` needs to be adjusted as well.
            self._send(
                Message.samples(
                    tree.samples,
                    path,
                    request=request,
                    totalMessages=count,
                )
            )

        # Recurse into sub-trees, but keep the total count
        for childPath, child in tree.children.items():
            self._sendTree(child, path + [childPath], request, count)

    async def _didReceiveDeletion(self, message: Message) -> None:
        """
        The central point to process deletion requests received over the
        connection.

        Args:
            message: The deletion request message received over the connection.

        Note:
            This function waits for the deletion to be completed and then sends
            an acknowledgement.
        """
        # Schedule the deletion
        request = self._storage.delete(
            message.path,
            message.time,
            message.end,
            message.depth,
        )

        # Check if the request expects a response
        if message.id is None:
            return

        # Wait for the delete to complete
        # TODO: Dispatch to the background to not block other requests from
        # being processed?
        await request

        self._send(Message.acknowledge(message.id, message.path))

    # MARK: - Message Receiver

    @override
    @synchronized
    async def acceptMessage(self, message: Message) -> None:
        """
        The central point where all received messages are processed.

        Args:
            message: The message received over the connection.

        Note:
            This function is called automatically by the connection, and should
            not be called manually.
        """
        match message.type:
            case MessageType.DATA:
                await self._didReceiveData(message)

            case MessageType.REQUEST:
                await self._didReceiveRequest(message)

            case MessageType.DELETION:
                await self._didReceiveDeletion(message)

            case (
                MessageType.SUBSCRIPTION_INCLUSION
                | MessageType.SUBSCRIPTION_DELETION
                | MessageType.SUBSCRIPTION_EXCLUSION
            ):
                return

    # MARK: - Storage

    @override
    def accept(self, tree: SampleTree, path: Path) -> Request:
        """
        Receive a request to store a tree for a path.

        The provided tree can contain multiple values for each node, and be of
        arbitrary depth.

        Components may choose to ignore parts of the tree due to access rights
        or other reasons.

        Args:
            tree: The tree to store.
            path: The path of the root node of the provided tree.

        Returns:
            A request handle, to optionally wait until the data is stored.

        Note:
            This function is not marked ``async`` in Swift because it is viewed
            as a request to store data. To wait until the data is stored, use
            ``commit()``.

        See Also:
            ``commit()``
        """
        return self._storage.accept(tree, path)

    @override
    async def tree(
        self,
        path: Path = Path(),
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
        limitPerNode: int | None = None,
    ) -> SampleTree:
        """
        Read a data tree for a given path within a given interval.

        This is the singular function to serve all data retrieval needs.

        The sort order of the result is:
        - ascending, if ``end is None``
        - descending, if ``end is not None`` and ``start is None``
        - ascending, if ``start < end``
        - descending, if ``start > end``

        The ``limitPerNode`` is applied in sort order.

        Args:
            path: The requested path.
            start: The start of the requested interval (exclusive).
            end: The end of the requested interval (inclusive).
            depth: The number of levels below the path to include.
            limitPerNode: The maximum number of values per node.

        Returns:
            The requested sample tree.

        Note:
            This function is asynchronous because providing the data may take
            some time.
        """
        return await self._storage.tree(
            path,
            start,
            end,
            depth,
            limitPerNode,
        )

    @override
    def delete(
        self,
        path: Path = Path(),
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
    ) -> Request:
        """
        Delete data from the storage.

        Args:
            path: The path of the node targeted for deletion.
            start: The start of the interval to delete (exclusive).
            end: The end of the interval to delete (inclusive).
            depth: The number of levels to include for deletion below the given
                path.

        Returns:
            A request that can be used to wait until completion.
        """
        return self._storage.delete(path, start, end, depth)

    # MARK: Connection

    @override
    async def isOpen(self) -> bool:
        return await self.connection.isOpen()

    @override
    @synchronized
    async def close(self) -> None:
        await self.connection.close()
        await self.shutdown()

    @override
    def onClose(self, perform: Callable[[], None] | None) -> Request:
        return self.connection.onClose(perform)
