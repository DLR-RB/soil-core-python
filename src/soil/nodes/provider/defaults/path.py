
from ..typed import PathProviderNode
from .node import DefaultProviderNode


class DefaultPathProviderNode(DefaultProviderNode, PathProviderNode):
    """
    A node that provides paths.
    """
