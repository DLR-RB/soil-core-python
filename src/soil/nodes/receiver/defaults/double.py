from soil.components import Receiver
from soil.data import Path

from ..typed import DoubleReceiverNode
from .node import DefaultReceiverNode


class DefaultDoubleReceiverNode(DefaultReceiverNode, DoubleReceiverNode):
    """
    A node that can receive doubles.
    """

    def __init__(self, receiver: Receiver, path: Path) -> None:
        """
        Create a node that can receive doubles.

        :param receiver: The receiver of the values.
        :param path: The path of the node in the tree.
        """
        super().__init__(receiver, path)
