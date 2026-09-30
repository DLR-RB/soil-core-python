
from ...provider.typed import PathProviderNode
from ...receiver.typed import PathReceiverNode
from ..node import StorageNode


class PathStorageNode(StorageNode, PathProviderNode, PathReceiverNode):
    """
    A node in the data tree that contains paths.
    """
