from typing import override

from ..components import ObservableStorage, Storage
from ..data import Path, SampleTree, Timestamp
from ..messaging import Message, MessageConnection, MessageReceiver, MessageType
from ..requests import Request
from .hosted_observable import HostedObservable
from .hosted_storage import HostedStorage


class HostedObservableStorage(Storage, MessageReceiver):
    """
    Expose an observable storage over an interface.

    It internally creates a ``HostedObservable`` and ``HostedStorage``,
    and distributes messages from the component to both objects.
    """

    def __init__(self, observable: HostedObservable, storage: HostedStorage):
        self._observable = observable
        """ The exposed observable managing the subscriptions """

        self._storage = storage
        """ The exposed storage """

    @classmethod
    async def create(
        cls,
        observable: ObservableStorage,
        connection: MessageConnection,
    ) -> 'HostedObservableStorage':
        """
        Host an observable storage over a connection.

        Args:
            observable: The observable storage to expose.
            connection: The connection over which to expose the observable
                storage.
        """

        # Note: Currently incoming data will be echoed back if the remote
        # subscribes to the path. This could lead to infinite loops.
        _observable = await HostedObservable.create(
            observable,
            connection,
        )
        _storage = await HostedStorage.create(
            observable,
            connection,
        )

        self = cls(_observable, _storage)

        # Receive messages in this class, and redistribute to the parts
        await connection.setReceiver(self)

        return self

    @property
    def connection(self) -> MessageConnection:
        """The connection to the remote."""
        return self._observable.connection

    # MARK: - Message Receiver

    @override
    def acceptMessage(self, message: Message) -> Request:
        """
        Insertion point for messages received over the connection.

        Subscription messages are forwarded to the contained observable,
        while data, requests, and deletions are forwarded to the wrapped
        storage.

        Args:
            message: The message received over the connection.

        Note:
            This function is called automatically by the connection, and
            should not be called manually.
        """
        match message.type:
            case (
                MessageType.DATA
                | MessageType.REQUEST
                | MessageType.DELETION
            ):
                return self._storage.acceptMessage(message)

            case (
                MessageType.SUBSCRIPTION_INCLUSION
                | MessageType.SUBSCRIPTION_EXCLUSION
                | MessageType.SUBSCRIPTION_DELETION
            ):
                return self._observable.acceptMessage(message)

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

        Note:
            In Swift this function is non-async because it represents a request
            to store data. In Python this implementation simply forwards the
            request asynchronously.

        See Also:
            commit()
        """
        return self._storage.accept(tree, path)

    async def tree(
        self,
        path: Path,
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
        return await self._storage.tree(path, start, end, depth, limitPerNode)

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
            depth: The number of levels below the path to include.

        Returns:
            A request that can be used to wait until completion.
        """
        return self._storage.delete(path, start, end, depth)

    async def shutdown(self):
        await self._storage.shutdown()