
from ..typed import DataProviderNode
from .node import DefaultProviderNode


class DefaultDataProviderNode(DefaultProviderNode, DataProviderNode):
    """
    A node that provides data.
    """
