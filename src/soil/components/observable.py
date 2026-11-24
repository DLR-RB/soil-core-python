from abc import abstractmethod

from ..data import Path, SampleTree
from ..requests import Request
from .distributor import Distributor


class Observable(Distributor):
    """
    A component that tracks and responds to subscriptions.

    The name `Observable` was chosen to indicate that changes to the data of the component can be monitored using subscriptions.

    Rejected terms include:
    - Broker: Implies negotiating data transfer
    - Dispatcher: Implies scheduling
    - Notifier: Suggests limited agency of clients, 'notification' suggests only events, not complete data
    - Publisher: Not clear that observers request which data to receive
    """

    @abstractmethod
    def include(self, path: Path, depth: int | None = None) -> Request:
        """
        Include a path in the subscription.

        Parameters
        ----------
        path: Path
            The path to include
        depth: int | None
            The depth of the inclusion (nil indicates the full sub-tree)

        Returns
        -------
        Request
            A request to wait for completion of the inclusion
        """

    @abstractmethod
    def exclude(self, path: Path, depth: int | None = None) -> Request:
        """
        Exclude a path from the subscription.

        Parameters
        ----------
        path: Path
            The path to exclude
        depth: int | None
            The depth of the exclusion (nil indicates the full sub-tree)

        Returns
        -------
        Request
            A request to wait for completion of the exclusion
        """

    @abstractmethod
    def deleteRules(self, path: Path, depth: int | None = None) -> Request:
        """
        Delete subscription rules at a path with a given depth

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

    @abstractmethod
    async def isSubscribed(self, path: Path) -> bool:
        """
        Check if a particular path is covered by the current subscription rules.

        Parameters
        ----------
        path: Path
            The path to check against the subscription rules

        Returns
        -------
        bool
            `true`, if the path matches
        """

    @abstractmethod
    async def reduce(self, tree: SampleTree, path: Path) -> SampleTree | None:
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
            The reduced tree, if any inclusion rules match, otherwise `None`
        """

    async def dataForReceiver(self, tree: SampleTree, path: Path) -> tuple[SampleTree, Path] | None:
        """
        Reduce a tree at a path to contain only the subscribed data.

        Parameters
        ----------
        tree: SampleTree
            The original tree to strip
        path: Path
            The path of the tree in relation to the subscription tree

        Returns
        -------
        Tuple[SampleTree, Path] | None
            The reduced tree with a possible sub-path, if any inclusion rules match, otherwise `None`
        """
        # Filter the data according to the subscription rules
        reduced = await self.reduce(tree, path)
        if reduced is None:
            return None

        # Select only the smallest tree,
        # in case the subscription rules removed some parts
        # that left only a single path at the root
        subPath, subTree = reduced.containedTree()
        return subTree, path + subPath

    async def distribute(self, tree: SampleTree, path: Path) -> None:
        """
        Forward the tree and path if it matches the subscription rules.

        Parameters
        ----------
        tree: SampleTree
            The tree to distribute
        path: Path
            The path of the tree
        """
        # Get the receiver of the subscription data
        receiver = await self.getReceiver()
        if receiver is None:
            return

        data = await self.dataForReceiver(tree, path)
        if data is None:
            return
        subscribedTree, subscribedPath = data

        await receiver.accept(subscribedTree, subscribedPath).wait()

