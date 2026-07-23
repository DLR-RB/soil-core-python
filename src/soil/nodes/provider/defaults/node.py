
from ...provider.node import ProviderNode
from ...tree import DefaultTreeNode

from typing import TYPE_CHECKING, override
if TYPE_CHECKING:
    from ....components import Provider
    from ....data import Path

class DefaultProviderNode(DefaultTreeNode, ProviderNode):
    """
    A node that has a provider.
    """

    def __init__(self, provider: Provider, path: Path) -> None:
        """
        Create a node that provides values.

        :param provider: The provider of the values.
        :param path: The path of the node in the tree.
        """
        super().__init__(path)

        self._provider = provider

    @override
    def provider(self) -> Provider:
        """
        Get the provider attached to this node.

        :return: The provider of the values.
        """
        return self._provider
