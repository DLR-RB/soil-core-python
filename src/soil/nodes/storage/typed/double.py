
from ...provider.typed import DoubleProviderNode
from ...receiver.typed import DoubleReceiverNode

from ..node import StorageNode


class DoubleStorageNode(StorageNode, DoubleProviderNode, DoubleReceiverNode):
    """
    A node in the data tree that contains doubles.
    """
    pass
