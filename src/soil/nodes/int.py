from abc import abstractmethod

from ..requests import Request

from .any import AnyStorageNode


class IntStorageNode(AnyStorageNode):
    """
    A node in the data tree that contains integers.
    """

    @abstractmethod
    def setInteger(self, value: int) -> Request:
        """
        Set the node to a value.

        Parameters
        ----------
        value: int
            The new value to set for this node.

        Returns
        -------
        Request
            A request to wait for completion.
        """
        raise NotImplementedError()

    @abstractmethod
    async def integerValue(self) -> int | None:
        """
        Get the current value of the node.

        Returns
        -------
        int | None
            The current value, or ``None`` if no value exists,
            or the current value is not a float.
        """
        raise NotImplementedError()
