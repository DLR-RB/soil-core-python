from soil.components import Receiver
from soil.data import Path
from .node import DefaultReceiverNode
from ..typed import DoubleReceiverNode


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
