
from ..typed import IntStorageNode
from .node import DefaultStorageNode


class DefaultIntStorageNode(DefaultStorageNode, IntStorageNode):
    """
    A node in a tree that is expected to contain integers as the value.
    """
    pass
