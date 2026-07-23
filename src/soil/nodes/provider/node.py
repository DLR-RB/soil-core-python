from abc import abstractmethod

from soil.components import Provider
from soil.data import Sample, SampleTree, Timestamp, Value
from soil.nodes.tree import TreeNode

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from soil.nodes.provider.defaults import *
    from soil.nodes.provider.typed import *


class ProviderNode(TreeNode):
    """
    A node in the tree of a provider.
    """

    @abstractmethod
    def provider(self) -> Provider:
        """
        Get the provider attached to this node.

        :return: The provider of the node data.
        """
        ...

    # MARK: Get

    async def isNull(self) -> bool | None:
        """
        Check if the current value at this node is null.

        :return: True if the value is null, False otherwise, or None if no value exists.
        """
        value = await self.currentValue()

        if value is None:
            return None

        return value.isNull

    async def currentValue(self) -> Value | None:
        """
        Get the current value.

        :return: The current value.
        """
        sample = await self.currentSample()

        if sample is None:
            return None
        return sample.value

    async def currentSample(self) -> Sample | None:
        """
        Provide the current sample.

        :return: The most recent sample at this node.
        """
        return await self.provider().currentSample(self.path())

    async def sample(self, beforeOrAt: Timestamp | None) -> Sample | None:
        """
        Get the value for the node at a specific point in time.

        The closest sample older than or equal to the provided timestamp is returned.

        :param beforeOrAt: The instant for which to get the value of the node.
        :return: The sample containing the value of the node at the given time.
        """
        return await self.provider().sample(self.path(), beforeOrAt)

    async def currentTree(self, depth: int | None = None) -> SampleTree:
        """
        Get the current values of a path, including sub-paths.

        :param depth: The maximum depth of the subtree to include.
        :return: The specified subtree at the current point in time.
        """
        return await self.provider().tree(
            self.path(),
            None,
            Timestamp.current(),
            depth,
            1,
        )

    def child(self, name: str) -> ProviderNode:
        """
        Create a generic node for a child of this node.

        :param name: The name of the child.
        :return: The node representing the child.
        """
        from .defaults.node import DefaultProviderNode
        return DefaultProviderNode(
            self.provider(),
            self.path().appending(name),
        )

    # MARK: Children

    def intChild(self, name: str) -> IntProviderNode:
        """
        Create a typed node for a child of this node that provides integers.
        """
        from .defaults.int import DefaultIntProviderNode
        return DefaultIntProviderNode(
            self.provider(),
            self.path().appending(name),
        )

    def doubleChild(self, name: str) -> DoubleProviderNode:
        """
        Create a typed node for a child of this node that provides doubles.
        """
        from .defaults.double import DefaultDoubleProviderNode
        return DefaultDoubleProviderNode(
            self.provider(),
            self.path().appending(name),
        )

    def stringChild(self, name: str) -> StringProviderNode:
        """
        Create a typed node for a child of this node that provides strings.
        """
        from .defaults.string import DefaultStringProviderNode
        return DefaultStringProviderNode(
            self.provider(),
            self.path().appending(name),
        )

    def dataChild(self, name: str) -> DataProviderNode:
        """
        Create a typed node for a child of this node that provides data.
        """
        from .defaults.data import DefaultDataProviderNode
        return DefaultDataProviderNode(
            self.provider(),
            self.path().appending(name),
        )

    def pathChild(self, name: str) -> PathProviderNode:
        """
        Create a typed node for a child of this node that provides paths.
        """
        from .defaults.path import DefaultPathProviderNode
        return DefaultPathProviderNode(
            self.provider(),
            self.path().appending(name),
        )
