from __future__ import annotations

from typing import TYPE_CHECKING, override

from ...tree import DefaultTreeNode
from ..node import StorageNode

if TYPE_CHECKING:
    from ....components import Storage
    from ....data import Path


class DefaultStorageNode(DefaultTreeNode, StorageNode):
    """
    A node that contains values.
    """

    def __init__(self, storage: Storage, path: Path) -> None:
        """
        Create a node that contains values.

        :param storage: The underlying storage to use.
        :param path: The path of the node in the tree.
        """
        super().__init__(path)
        self._storage = storage

    @override
    def storage(self) -> Storage:
        """
        Get the storage attached to this node.

        :return: The underlying storage.
        """
        return self._storage
