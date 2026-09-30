
from ..typed import IntProviderNode
from .node import DefaultProviderNode


class DefaultIntProviderNode(DefaultProviderNode, IntProviderNode):
    """
    A node that provides integers.
    """
