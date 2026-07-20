from abc import abstractmethod

from ..requests import Request

from .any import AnyStorageNode


class DoubleStorageNode(AnyStorageNode):
    """
    A node in the data tree that contains doubles.
    """

    @abstractmethod
    def setDouble(self, value: float) -> Request:
        """
        Set the node to a value.

        Parameters
        ----------
        value: float
            The new value to set for this node.

        Returns
        -------
        Request
            A request to wait for completion.
        """
        raise NotImplementedError()

    @abstractmethod
    async def doubleValue(self) -> float | None:
        """
        Get the current value of the node.

        Returns
        -------
        float | None
            The current value, or ``None`` if no value exists,
            or the current value is not a float.
        """
        raise NotImplementedError()
