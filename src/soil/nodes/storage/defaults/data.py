
from ..typed import DataStorageNode
from .node import DefaultStorageNode


class DefaultDataStorageNode(DefaultStorageNode, DataStorageNode):
    """
    A node in a tree that is expected to contain data as the value.
    """
    pass
