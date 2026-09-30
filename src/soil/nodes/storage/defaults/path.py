
from ..typed import PathStorageNode
from .node import DefaultStorageNode


class DefaultPathStorageNode(DefaultStorageNode, PathStorageNode):
    """
    A node in a tree that is expected to contain paths as the value.
    """
