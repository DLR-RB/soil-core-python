
from ...provider.typed import IntProviderNode
from ...receiver.typed import IntReceiverNode
from ..node import StorageNode


class IntStorageNode(StorageNode, IntProviderNode, IntReceiverNode):
    """
    A node in the data tree that contains integers.
    """
