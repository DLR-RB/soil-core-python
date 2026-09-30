from soil.components import Receiver
from soil.data import Path

from ..typed import IntReceiverNode
from .node import DefaultReceiverNode


class DefaultIntReceiverNode(DefaultReceiverNode, IntReceiverNode):
    """
    A node that can receive integers.
    """

    def __init__(self, receiver: Receiver, path: Path) -> None:
        """
        Create a node that can receive integers.

        :param receiver: The receiver of the values.
        :param path: The path of the node in the tree.
        """
        super().__init__(receiver, path)
