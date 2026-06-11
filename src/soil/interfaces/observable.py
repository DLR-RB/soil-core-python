from abc import ABC, abstractmethod
from typing import Tuple

from ..data import Path, SampleTree
from ..requests import Request

from .receiver import Receiver


class Observable(ABC):
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
    def setReceiver(self, receiver: Receiver | None) -> None:
        """
        Set the receiver for subscription data
        - Parameter receiver: The receiver of data matching the subscription rules
        - Returns: A request to optionally wait for completion
        """
        pass

    @abstractmethod
    def getReceiver(self) -> Receiver | None:
        """
        Get the receiver for matching data.
        - Returns: The receiver, if set
        """
        pass

    @abstractmethod
    def include(self, path: Path, depth: int | None) -> Request:
        """
        Include a path in the subscription.
        - Parameter path: The path to include
        - Parameter depth: The depth of the inclusion (nil indicates the full sub-tree)
        - Returns: A request to wait for completion of the inclusion
        """
        pass

    @abstractmethod
    def exclude(self, path: Path, depth: int | None) -> Request:
        """
        Exclude a path from the subscription.
        - Parameter path: The path to exclude
        - Parameter depth: The depth of the exclusion (nil indicates the full sub-tree)
        - Returns: A request to wait for completion of the exclusion
        """
        pass

    @abstractmethod
    def deleteRules(self, path: Path, depth: int | None) -> Request:
        """
        Delete subscription rules at a path with a given depth
        - Parameter path: The path for which to delete rules
        - Parameter depth: The depth of the deletion
        - Returns: A request to wait for completion of the deletion
        """
        pass

    @abstractmethod
    def isSubscribed(self, path: Path) -> bool:
        """
        Check if a particular path is covered by the current subscription rules.
        - Parameter path: The path to check against the subscription rules
        - Returns: `true`, if the path matches
        """
        pass

    @abstractmethod
    def reduce(self, tree: SampleTree, path: Path) -> SampleTree | None:
        """
        Use the subscription rules to remove all excluded parts of a tree.
        - Parameter tree: The original tree to strip
        - Parameter path: The path of the tree in relation to the subscription tree
        - Returns: The reduced tree, if any inclusion rules match, otherwise `null`
        """
        pass

    async def dataForReceiver(self, tree: SampleTree, path: Path) -> Tuple[SampleTree, Path] | None:
        """
        Reduce a tree at a path to contain only the subscribed data.
        """
        # Filter the data according to the subscription rules
        reduced = self.reduce(tree, path)
        if reduced is None:
            return None

        # Select only the smallest tree,
        # in case the subscription rules removed some parts
        # that left only a single path at the root
        subPath, subTree = reduced.containedTree()
        return subTree, path.appending(subPath)

    async def distribute(self, tree: SampleTree, path: Path) -> None:
        """
        Forward the tree and path if it matches the subscription rules.
        - Parameter tree: The tree to distribute
        - Parameter path: The path of the tree
        """
        # Get the receiver of the subscription data
        receiver = self.getReceiver()
        if receiver is None:
            return

        data = await self.dataForReceiver(tree, path)
        if data is None:
            return
        subscribedTree, subscribedPath = data

        await receiver.receive(subscribedTree, subscribedPath).wait()
