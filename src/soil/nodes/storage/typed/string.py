
from ...provider.typed import StringProviderNode
from ...receiver.typed import StringReceiverNode
from ..node import StorageNode


class StringStorageNode(StorageNode, StringProviderNode, StringReceiverNode):
    """
    A node in the data tree that contains doubles.
    """
