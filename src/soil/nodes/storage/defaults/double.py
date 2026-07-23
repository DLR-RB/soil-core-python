
from ..typed import DoubleStorageNode
from .node import DefaultStorageNode


class DefaultDoubleStorageNode(DefaultStorageNode, DoubleStorageNode):
    """
    A node in a tree that is expected to contain doubles as the value.
    """
    pass
