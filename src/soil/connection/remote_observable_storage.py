from typing import override

from ..components import Observable, Storage, Receiver
from ..data import Path, SampleTree, Timestamp
from ..messaging import MessageConnection, Message, MessageReceiver, MessageType
from ..requests import Request, AsyncRequest
from ..transport import Connection

from .remote_storage import RemoteStorage
from .remote_observable import RemoteObservable


class RemoteObservableStorage(MessageReceiver, Observable, Storage):

    """
    Create a connection to an observable storage over a connection.
    """
    def __init__(self, observable: RemoteObservable, storage: RemoteStorage):
        self._observable = observable
        """ The object managing the subscriptions to the remote """

        self._storage = storage
        """ The object managing the storage interface to the remote """

    @classmethod
    async def create(cls, connection: MessageConnection) -> 'RemoteObservableStorage':
        """
        Parameters
        ----------
        connection: MessageConnection
            The connection where the component is hosted.
        """
        observable = await RemoteObservable.create(connection=connection)
        storage = await RemoteStorage.create(connection=connection)

        instance = cls(observable, storage)

        await connection.setReceiver(instance).wait()
        return instance

    @property
    def connection(self) -> Connection:
        """The connection to the remote"""
        return self._observable.connection

    # MARK: Message receiver

    """
    Callback to receive messages from the remote component.

    Parameters
    ----------
    message: Message
        The message received over the connection

    :note: This function is called automatically by the connection, and should not be called manually.
    """
    @override
    def acceptMessage(self, message: Message) -> Request:
        if message.type == MessageType.DATA:
            async def operation():
                await self._storage.acceptMessage(message)
                await self._observable.acceptMessage(message)

            return AsyncRequest(operation())

        if message.type == MessageType.REQUEST:
            return self._storage.acceptMessage(message)

        if message.type == MessageType.DELETION:
            return self._storage.acceptMessage(message)

        if message.type in (
            MessageType.SUBSCRIPTION_INCLUSION,
            MessageType.SUBSCRIPTION_DELETION,
            MessageType.SUBSCRIPTION_EXCLUSION,
        ):
            return self._observable.acceptMessage(message)

        raise ValueError(f"Unsupported message type: {message.type}")

    # MARK: Observable

    """
    Set the receiver for subscription data.

    Parameters
    ----------
    receiver: Receiver | None
        The receiver of data matching the subscription rules

    Returns
    -------
    Request
        A request to optionally wait for completion
    """
    @override
    def setReceiver(self, receiver: Receiver | None) -> Request:
        return self._observable.setReceiver(receiver)

    """
    Get the receiver for matching data.

    Returns
    -------
    Receiver | None
        The receiver, if set
    """
    @override
    async def getReceiver(self) -> Receiver | None:
        return await self._observable.getReceiver()

    """
    Include a path in the subscription.

    Parameters
    ----------
    path: Path
        The path to include
    depth: int | None
        The depth of the inclusion (None indicates the full sub-tree)

    Returns
    -------
    Request
        A request to wait for completion of the inclusion
    """
    @override
    def include(self, path: Path, depth: int | None) -> Request:
        return AsyncRequest(self._observable.include(path, depth=depth))

    """
    Exclude a path from the subscription.

    Parameters
    ----------
    path: Path
        The path to exclude
    depth: int | None
        The depth of the exclusion (None indicates the full sub-tree)

    Returns
    -------
    Request
        A request to wait for completion of the exclusion
    """
    @override
    def exclude(self, path: Path, depth: int | None) -> Request:
        return AsyncRequest(self._observable.exclude(path, depth=depth))

    """
    Delete subscription rules at a path with a given depth.

    Parameters
    ----------
    path: Path
        The path for which to delete rules
    depth: int | None
        The depth of the deletion

    Returns
    -------
    Request
        A request to wait for completion of the deletion
    """
    @override
    def deleteRules(self, path: Path, depth: int | None = None) -> Request:
        return AsyncRequest(self._observable.deleteRules(path, depth=depth))

    """
    Check if a particular path is covered by the current subscription rules.

    :param path: The path to check against the subscription rules
    :returns: True if the path matches
    """
    @override
    async def isSubscribed(self, path: Path) -> bool:
        return await self._observable.isSubscribed(path)

    """
    Use the subscription rules to remove all excluded parts of a tree.

    Parameters
    ----------
    tree: SampleTree
        The original tree to strip
    path: Path
        The path of the tree in relation to the subscription tree

    Returns
    -------
    SampleTree | None
        The reduced tree, if any inclusion rules match, otherwise None
    """
    @override
    async def reduce(self, tree: SampleTree, path: Path) -> SampleTree | None:
        return await self._observable.reduce(tree, path)

    # MARK: Storage

    """
    Receive a tree for a path.

    This is the singular function to inject data into a component.

    The provided tree can contain multiple values for each node, and be of arbitrary depth.

    Components may choose to ignore parts of the tree due to access rights or other reasons.

    Parameters
    ----------
    tree: SampleTree
        The tree to store.
    path: Path
        The path of the root node of the provided tree

    :note: This function is not async, because it is viewed as a request to store data.
           The data does not actually need to be stored when the function returns,
           and should return as fast as possible.
    """
    @override
    def accept(self, tree: SampleTree, path: Path) -> Request:
        return self._storage.accept(tree, path)

    """
    Read a data tree for a given path within a given interval.

    This is the singular function to serve all data retrieval needs.

    The sort order of the result is:
    - ascending, if `end = None`
    - descending, if `end != None` and `start = None`
    - ascending, if `start < end`
    - descending, if `start > end`

    The `limitPerNode` is applied in sort order.

    Parameters
    ----------
    path: Path
        The requested path.
    start: Timestamp | None
        The start of the requested interval (exclusive, defaults to None,
        meaning from beginning of time)
    end: Timestamp | None
        The end of the requested interval (inclusive, defaults to None,
        meaning to end of time)
    depth: int | None
        The number of levels below the path to include in the result
    limitPerNode: int | None
        The maximum number of values to return for each node of
        the tree (defaults to None, i.e. no limit)

    Returns
    -------
    SampleTree
        The tree with the given depth, limited to the maximum count per
        node, for the requested interval.

    :note: This function is async because providing the data may take some time.
           It could be retrieved over a network, from an otherwise slow database,
           or from other components.
    """
    @override
    async def tree(
        self,
        path: Path,
        start: Timestamp | None,
        end: Timestamp | None,
        depth: int | None,
        limitPerNode: int | None,
    ) -> SampleTree:
        return await self._storage.tree(
            path,
            start,
            end,
            depth,
            limitPerNode,
        )

    """
    Delete data from the storage.

    Parameters
    ----------
    path: Path
        The path of the node targeted for the delete.
    start: Timestamp | None
        The start of the interval to delete (exclusive, defaults to None,
        meaning from beginning of time)
    end: Timestamp | None
        The end of the interval to delete (inclusive, defaults to None,
        meaning to end of time)
    depth: int | None
        The number of levels to include for deletion below the given path
    """
    @override
    def delete(
        self,
        path: Path = Path(),
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
    ) -> Request:
        return self._storage.delete(
            path = path,
            start = start,
            end = end,
            depth = depth,
        )
