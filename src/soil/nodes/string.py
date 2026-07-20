from abc import abstractmethod

from ..requests import Request

from .any import AnyStorageNode


class StringStorageNode(AnyStorageNode):
    """
    A node in the data tree that contains strings.
    """

    @abstractmethod
    def setString(self, value: str) -> Request:
        """
        Set the node to a value.

        Parameters
        ----------
        value: str
            The new value to set for this node.

        Returns
        -------
        Request
            A request to wait for completion.
        """
        raise NotImplementedError()

    @abstractmethod
    async def stringValue(self) -> str | None:
        """
        Get the current value of the node.

        Returns
        -------
        str | None
            The current value, or ``None`` if no value exists,
            or the current value is not a string.
        """
        raise NotImplementedError()
