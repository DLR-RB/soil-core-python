
from ..typed import StringStorageNode
from .node import DefaultStorageNode


class DefaultStringStorageNode(DefaultStorageNode, StringStorageNode):
    """
    A node in a tree that is expected to contain strings as the value.
    """
    pass
