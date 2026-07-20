from abc import abstractmethod

from ..requests import Request

from .any import AnyStorageNode


class DataStorageNode(AnyStorageNode):
    """
    A node in the data tree that contains binary data.
    """

    @abstractmethod
    def setData(self, value: bytes) -> Request:
        """
        Set the node to a value.

        Parameters
        ----------
        value: bytes
            The new value to set for this node.

        Returns
        -------
        Request
            A request to wait for completion.
        """
        raise NotImplementedError()

    @abstractmethod
    async def dataValue(self) -> bytes | None:
        """
        Get the current value of the node.

        Returns
        -------
        bytes | None
            The current value, or ``None`` if no value exists,
            or the current value is not binary data.
        """
        raise NotImplementedError()
