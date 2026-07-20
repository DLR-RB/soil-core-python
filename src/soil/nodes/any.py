from abc import ABC, abstractmethod

from ..data import Timestamp
from ..requests import Request

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .storage import StorageNode


class AnyStorageNode(ABC):

    @abstractmethod
    def setNull(self) -> Request:
        """
        Returns:
            A request that can be used to wait until completion.
        """
        raise NotImplementedError()

    @abstractmethod
    def deleteAtNode(
        self,
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
    ) -> Request:
        """
        Delete data from the node.

        Args:
            start: The start of the interval to delete (exclusive,
                defaults to ``None``, meaning from the beginning of time).
            end: The end of the interval to delete (inclusive,
                defaults to ``None``, meaning to the end of time).
            depth: The number of levels to include for deletion below
                the given path.

        Returns:
            A request that can be used to wait until completion.
        """
        raise NotImplementedError

    @abstractmethod
    def child(self, named: str) -> 'StorageNode':
        """
        Create a generic storage node for a child of this node.

        Args:
            named: The name of the child.

        Returns:
            The node representing the child.
        """
        raise NotImplementedError()