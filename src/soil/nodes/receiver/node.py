from typing import TYPE_CHECKING
from abc import abstractmethod

from soil.components import Receiver
from soil.data import Sample, SampleTree, Timestamp, Value
from ..tree import TreeNode

if TYPE_CHECKING:
    from soil.nodes.receiver.defaults import *
    from soil.nodes.receiver.typed import *


class ReceiverNode(TreeNode):
    """
    A node in the tree of a receiver.
    """

    @abstractmethod
    def receiver(self) -> Receiver:
        """
        The receiver attached to this node.

        :return: The receiver of the data.
        """
        ...

    # MARK: Set

    async def set(self, value: Value, timestamp: Timestamp | None = None) -> None:
        """
        Ingest a new value.

        If no timestamp is provided, the current timestamp is used.

        :param value: The new value for the node.
        :param timestamp: Optional timestamp associated with the value.
        """
        await self.receiver().acceptValue(value, self.path(), timestamp)

    async def setNull(self) -> None:
        """
        Set the node to null.
        """
        await self.set(Value(None))

    async def setSample(self, sample: Sample) -> None:
        """
        Ingest a new timestamped value.

        :param sample: The sample to set.
        """
        await self.receiver().acceptSample(sample, self.path())

    async def setSamples(self, samples: list[Sample]) -> None:
        """
        Ingest samples for the node.

        :param samples: The samples to store.
        """
        await self.receiver().acceptSamples(samples, self.path())

    async def setTree(self, tree: SampleTree) -> None:
        """
        Ingest a tree.

        :param tree: The tree to store.
        """
        await self.receiver().accept(tree, self.path())

    def childReceiver(self, name: str) -> ReceiverNode:
        """
        Create a generic node for a child of this node.

        :param name: The name of the child.
        :return: The node representing the child.
        """
        return DefaultReceiverNode(self.receiver(), self.path().appending(name))

    # MARK: Children

    def intChild(self, name: str) -> IntReceiverNode:
        """
        Create a typed node for a child of this node that receives integers.
        """
        from .defaults.int import DefaultIntReceiverNode
        return DefaultIntReceiverNode(
            self.receiver(),
            self.path().appending(name),
        )

    def doubleChild(self, name: str) -> DoubleReceiverNode:
        """
        Create a typed node for a child of this node that receives doubles.
        """
        from .defaults.double import DefaultDoubleReceiverNode
        return DefaultDoubleReceiverNode(
            self.receiver(),
            self.path().appending(name),
        )

    def stringChild(self, name: str) -> StringReceiverNode:
        """
        Create a typed node for a child of this node that receives strings.
        """
        from .defaults.string import DefaultStringReceiverNode
        return DefaultStringReceiverNode(
            self.receiver(),
            self.path().appending(name),
        )

    def dataChild(self, name: str) -> DataReceiverNode:
        """
        Create a typed node for a child of this node that receives data.
        """
        from .defaults.data import DefaultDataReceiverNode
        return DefaultDataReceiverNode(
            self.receiver(),
            self.path().appending(name),
        )

    def pathChild(self, name: str) -> PathReceiverNode:
        """
        Create a typed node for a child of this node that receives paths.
        """
        from .defaults.path import DefaultPathReceiverNode
        return DefaultPathReceiverNode(
            self.receiver(),
            self.path().appending(name),
        )
