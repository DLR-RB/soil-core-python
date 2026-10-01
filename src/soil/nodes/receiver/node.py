from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, override

from soil.data.path import Path

from ...components import Receiver
from ...data import Sample, SampleTree, Timestamp, Value
from ...requests import Request
from ..tree import TreeNode

if TYPE_CHECKING:
    from soil.nodes.receiver.defaults import *
    from soil.nodes.receiver.typed import *


class ReceiverNode(TreeNode, Receiver):
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

    def set(self, value: Value, timestamp: Timestamp | None = None) -> Request:
        """
        Ingest a new value.

        If no timestamp is provided, the current timestamp is used.

        :param value: The new value for the node.
        :param timestamp: Optional timestamp associated with the value.
        """
        return self.receiver().acceptValue(value, self.path(), timestamp)

    def setNull(self) -> Request:
        """
        Set the node to null.
        """
        return self.set(Value(None))

    def setSample(self, sample: Sample) -> Request:
        """
        Ingest a new timestamped value.

        :param sample: The sample to set.
        """
        return self.receiver().acceptSample(sample, self.path())

    def setSamples(self, samples: list[Sample]) -> Request:
        """
        Ingest samples for the node.

        :param samples: The samples to store.
        """
        return self.receiver().acceptSamples(samples, self.path())

    def setTree(self, tree: SampleTree) -> Request:
        """
        Ingest a tree.

        :param tree: The tree to store.
        """
        return self.receiver().accept(tree, self.path())

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

    # MARK: Receiver

    @override
    def accept(self, tree: SampleTree, path: Path) -> Request:
        return self.receiver().accept(tree, self.path() + path)
