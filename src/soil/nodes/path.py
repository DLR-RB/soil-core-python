from abc import abstractmethod

from ..data import Path
from ..requests import Request

from .any import AnyStorageNode


class PathStorageNode(AnyStorageNode):
    """
    A node in the data tree that contains paths.
    """

    @abstractmethod
    def setPath(self, value: Path) -> Request:
        """
        Set the node to a value.

        Parameters
        ----------
        value: Path
            The new value to set for this node.

        Returns
        -------
        Request
            A request to wait for completion.
        """
        raise NotImplementedError()

    @abstractmethod
    async def pathValue(self) -> Path | None:
        """
        Get the current value of the node.

        Returns
        -------
        Path | None
            The current value, or ``None`` if no value exists,
            or the current value is not a Path.
        """
        raise NotImplementedError()
