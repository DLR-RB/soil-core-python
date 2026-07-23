from typing import override

from soil.data import Path
from .tree import TreeNode


class DefaultTreeNode(TreeNode):
    """
    A node in a tree.
    """

    def __init__(self, path: Path) -> None:
        """
        Create a node in a tree.

        :param path: The path of the node.
        """
        self._path = path

    @override
    def path(self) -> Path:
        """
        Get the path of this node.

        :return: The path of this node.
        """
        return self._path