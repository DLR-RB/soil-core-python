from abc import ABC, abstractmethod

from soil.data import Path


class TreeNode(ABC):
    """
    A node in a data tree.
    """

    @abstractmethod
    def path(self) -> Path:
        """
        Get the path of this node.

        :return: The path of this node.
        """
