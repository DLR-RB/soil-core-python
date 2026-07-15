from abc import abstractmethod

from ..data import Path, Timestamp
from ..requests import Request
from .provider import Provider
from .receiver import Receiver


class Storage(Provider, Receiver):
    """
    A component that provides all operations required to store, retrieve, and delete data
    """

    @abstractmethod
    def delete(self, path: Path = Path(), start: Timestamp | None = None, end: Timestamp | None = None, depth: int | None = None) -> Request:
        """
        Delete data from the storage.

        Parameters
        ----------
        path: Path
            The path of the node targeted for the delete.
        start: Timestamp | None
            The start of the interval to delete (exclusive, defaults to `nil`, meaning from beginning of time)
        end: Timestamp | None
            The end of the interval to delete (inclusive, defaults to `nil`, meaning to end of time)
        depth: int | None
            The number of levels to include for deletion below the given path

        Returns
        -------
        Request
            A request that can be used to wait until completion
        """
        pass

    def deleteAtRoot(self, start: Timestamp | None, end: Timestamp | None, depth: int | None) -> Request:
        """
        Delete data from the storage.

        Parameters
        ----------
        start: Timestamp | None
            The start of the interval to delete (exclusive, defaults to `nil`, meaning from beginning of time)
        end: Timestamp | None
            The end of the interval to delete (inclusive, defaults to `nil`, meaning to end of time)
        depth: int | None
            The number of levels to include for deletion below the given path

        Returns
        -------
        Request
            A request that can be used to wait until completion
        """
        return self.delete(Path(), start, end, depth)

