from soil.components import Receiver
from soil.data import Path

from ..typed import StringReceiverNode
from .node import DefaultReceiverNode


class DefaultStringReceiverNode(DefaultReceiverNode, StringReceiverNode):
    """
    A node that can receive strings.
    """

    def __init__(self, receiver: Receiver, path: Path) -> None:
        """
        Create a node that can receive strings.

        :param receiver: The receiver of the values.
        :param path: The path of the node in the tree.
        """
        super().__init__(receiver, path)
