from __future__ import annotations

from soil.components import Receiver
from soil.data import Path
from soil.nodes.receiver.node import ReceiverNode
from soil.nodes.tree import DefaultTreeNode


class DefaultReceiverNode(DefaultTreeNode, ReceiverNode):
    """
    A node that can receive values.
    """

    def __init__(
        self,
        receiver: Receiver,
        path: Path,
    ) -> None:
        """
        Create a node that can receive values.

        :param receiver: The receiver of the values.
        :param path: The path of the node in the tree.
        """
        super().__init__(path)

        self._receiver = receiver

    def receiver(self) -> Receiver:
        return self._receiver