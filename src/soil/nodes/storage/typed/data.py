
from ...provider.typed import DataProviderNode
from ...receiver.typed import DataReceiverNode

from ..node import StorageNode


class DataStorageNode(StorageNode, DataProviderNode, DataReceiverNode):
    """
    A node in the data tree that contains binary data.
    """
    pass
