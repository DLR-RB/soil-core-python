from typing import override

from ..components import ObservableStorage, Receiver, Storage
from ..data import Path, SampleTree, Timestamp
from ..requests import Request
from ..subscriptions import SubscriptionTree
from ..utils import Actor, queuedAsync, synchronized


class ObservingStorage(Actor, ObservableStorage):
    """
    A wrapper to make a storage observable.

    Note: The storage should be shut down using `shutdown()` after use.
    """

    def __init__(self, wrapping: Storage):
        Actor.__init__(self)
        self._storage = wrapping

        # The subscriptions, indexed by their id.
        self._subscriptions = SubscriptionTree()

        # Subscription data receiver.
        self._receiver: Receiver | None = None

    # MARK: Observable

    @override
    @synchronized
    async def setReceiver(self, receiver: Receiver | None) -> None:
        """
        Set the receiver for subscription data.

        Args:
            receiver: The receiver of data matching the subscription rules.

        Returns:
            A request to optionally wait for completion.
        """
        self._receiver = receiver

    @override
    @queuedAsync
    def getReceiver(self) -> Receiver | None:
        """
        Get the receiver for matching data.

        Returns:
            The receiver, if set.
        """
        return self._receiver

    @override
    @synchronized
    async def include(
        self,
        path: Path,
        depth: int | None,
    ) -> None:
        """
        Include a path in the subscription.

        Args:
            path: The path to include.
            depth: The depth of the inclusion (`None` indicates the full
                sub-tree).

        Returns:
            A request to wait for completion of the inclusion.
        """
        self._subscriptions.include(path, depth=depth)

    @override
    @synchronized
    async def exclude(
        self,
        path: Path,
        depth: int | None,
    ) -> None:
        """
        Exclude a path from the subscription.

        Args:
            path: The path to exclude.
            depth: The depth of the exclusion (`None` indicates the full
                sub-tree).

        Returns:
            A request to wait for completion of the exclusion.
        """
        self._subscriptions.exclude(path, depth=depth)

    @override
    @synchronized
    async def deleteRules(
        self,
        path: Path,
        depth: int | None,
    ) -> None:
        """
        Delete subscription rules at a path with a given depth.

        Args:
            path: The path for which to delete rules.
            depth: The depth of the deletion.

        Returns:
            A request to wait for completion of the deletion.
        """
        self._subscriptions.deleteRules(path, depth=depth)

    @override
    @queuedAsync
    def isSubscribed(self, path: Path) -> bool:
        """
        Check if a particular path is covered by the current subscription
        rules.

        Args:
            path: The path to check against the subscription rules.

        Returns:
            ``True`` if the path matches.
        """
        return self._subscriptions.isSubscribed(path)

    @override
    @queuedAsync
    def reduce(
        self,
        tree: SampleTree,
        path: Path,
    ) -> SampleTree | None:
        """
        Use the subscription rules to remove all excluded parts of a tree.

        Args:
            tree: The original tree to strip.
            path: The path of the tree in relation to the subscription tree.

        Returns:
            The reduced tree, if any inclusion rules match, otherwise ``None``.
        """
        return self._subscriptions.reduce(tree, path)

    # MARK: Storage

    @override
    @synchronized
    async def accept(self, tree: SampleTree, path: Path = Path()) -> None:
        """
        Receive a tree for a path.

        Args:
            tree: The tree to store.
            forPath: The path associated with the samples.
        """

        if tree.isEmpty:
            return

        # Store the data, wait for completion so that the receive of this class
        # works as expected.
        await self._storage.accept(tree, path=path)

        # Forward the data to the subscription receiver, if needed.
        await self.distribute(tree=tree, path=path)

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
        - ascending, if `toTimestamp is None`
        - descending, if `toTimestamp is not None` and `fromTimestamp is None`
        - ascending, if `fromTimestamp < toTimestamp`
        - descending, if `fromTimestamp > toTimestamp`

        The `limitPerNode` is applied in sort order.

        Args:
            path: The requested path.
            start: The start of the requested interval (exclusive,
                defaults to ``None``).
            end: The end of the requested interval (inclusive,
                defaults to ``None``).
            depth: The number of levels below the path to include in the result.
            limitPerNode: The maximum number of values to return for each node.

        Returns:
            The requested tree.
        """
        return await self._storage.tree(path = path, start = start, end = end, depth = depth, limitPerNode = limitPerNode)

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
            path: The path of the node targeted for the delete.
            start: The start of the interval to delete (exclusive,
                defaults to ``None``).
            toTimestamp: The end of the interval to delete (inclusive,
                defaults to ``None``).
            depth: The number of levels to include for deletion below the given
                path.

        Returns:
            A request that can be used to wait until completion.
        """
        return self._storage.delete(path = path, start = start, end = end, depth = depth)
