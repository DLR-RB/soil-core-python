from abc import abstractmethod
from typing import TYPE_CHECKING, override

from ...components import Provider, Receiver, Storage
from ...data import Timestamp
from ..provider.node import ProviderNode
from ..receiver.node import ReceiverNode

if TYPE_CHECKING:
    from soil.nodes.storage.defaults import *
    from soil.nodes.storage.typed import *


class StorageNode(ProviderNode, ReceiverNode):
    """
    A node that provides storage.
    """

    @abstractmethod
    def storage(self) -> Storage:
        """
        The storage to which this node belongs.

        :return: The underlying storage.
        """
        ...

    @override
    def receiver(self) -> Receiver:
        """
        Get the receiver of the node.

        :return: The current receiver.
        """
        return self.storage()

    @override
    def provider(self) -> Provider:
        """
        Get the provider of the node.

        :return: The current provider.
        """
        return self.storage()

    @override
    def child(self, name: str) -> StorageNode:
        """
        Create a generic node for a child of this node.

        :param name: The name of the child.
        :return: The node representing the child.
        """
        from .defaults.node import DefaultStorageNode
        return DefaultStorageNode(
            self.storage(),
            self.path().appending(name),
        )

    # MARK: Deletion

    async def delete(self, start: Timestamp | None, end: Timestamp | None, depth: int | None) -> None:
        """
        Delete data from storage.

        :param start: The start of the interval to delete (exclusive, None indicates from beginning of time).
        :param end: The end of the interval to delete (inclusive, None indicates to end of time).
        :param depth: The number of levels to include for deletion below the given path.
                      None means the full subtree.
        """
        await self.storage().delete(
            self.path(),
            start,
            end,
            depth,
        )

    async def deleteHistory(self) -> None:
        """
        Delete all history for a path.

        :param path: The path of the node targeted for the delete.
        """
        await self.delete(start = None, end = None, depth = 0)

    async def deleteTree(self) -> None:
        """
        Delete all history of the complete subtree.
        """
        await self.delete(
            None,
            None,
            None,
        )

    # MARK: Children

    def intChild(self, name: str) -> IntStorageNode:
        """
        Create a typed node for a child of this node that stores integers.
        """
        from .defaults.int import DefaultIntStorageNode
        return DefaultIntStorageNode(
            self.storage(),
            self.path().appending(name),
        )

    def doubleChild(self, name: str) -> DoubleStorageNode:
        """
        Create a typed node for a child of this node that stores doubles.
        """
        from .defaults.double import DefaultDoubleStorageNode
        return DefaultDoubleStorageNode(
            self.storage(),
            self.path().appending(name),
        )

    def stringChild(self, name: str) -> StringStorageNode:
        """
        Create a typed node for a child of this node that stores strings.
        """
        from .defaults.string import DefaultStringStorageNode
        return DefaultStringStorageNode(
            self.storage(),
            self.path().appending(name),
        )

    def dataChild(self, name: str) -> DataStorageNode:
        """
        Create a typed node for a child of this node that stores data.
        """
        from .defaults.data import DefaultDataStorageNode
        return DefaultDataStorageNode(
            self.storage(),
            self.path().appending(name),
        )

    def pathChild(self, name: str) -> PathStorageNode:
        """
        Create a typed node for a child of this node that stores paths.
        """
        from .defaults.path import DefaultPathStorageNode
        return DefaultPathStorageNode(
            self.storage(),
            self.path().appending(name),
        )
