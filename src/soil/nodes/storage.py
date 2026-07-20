from typing import override

from ..components import Storage
from ..data import Path, SampleTree, Timestamp, Value
from ..requests import Request

from .data import DataStorageNode
from .double import DoubleStorageNode
from .int import IntStorageNode
from .path import PathStorageNode
from .string import StringStorageNode


class StorageNode(
    Storage,
    StringStorageNode,
    IntStorageNode,
    DoubleStorageNode,
    DataStorageNode,
    PathStorageNode,
):
    """
    A node in a data tree for a specific path.

    This node can also be viewed as a storage,
    except that it maps all operations to a sub-tree.
    """

    def __init__(self, storage: Storage, path: Path):
        """
        Create an interface to a node in a storage at a path.

        Args:
            storage: The storage to wrap.
            path: The path of the node in the tree.
        """
        self._storage = storage
        self.path = path

    # MARK: Provider

    @override
    async def tree(
        self,
        path: Path,
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
        limitPerNode: int | None = None,
    ) -> SampleTree:
        """
        Read a data tree for a given path within a given interval.

        This is the singular function to serve all data retrieval needs.

        The sort order of the result is:
        - ascending, if `toTimestamp is None`
        - descending, if `toTimestamp is not None` and `fromTimestamp is None`
        - ascending, if `fromTimestamp < toTimestamp`
        - descending, if `fromTimestamp > toTimestamp`

        The `limitPerNode` is applied in sort order.

        Args:
            path: The requested path.
            fromTimestamp: The start of the requested interval (exclusive,
                defaults to ``None``, meaning from the beginning of time).
            toTimestamp: The end of the requested interval (inclusive,
                defaults to ``None``, meaning to the end of time).
            depth: The number of levels below the path to include in the result.
            limitPerNode: The maximum number of values to return for each node
                of the tree.

        Returns:
            The tree with the given depth, limited to the maximum count per
            node, for the requested interval.

        Note:
            This function is asynchronous because providing the data may take
            some time. It could be retrieved over a network, from an otherwise
            slow database, or from other components.
        """
        return await self._storage.tree(
            path = self.path + path,
            start = start,
            end = end,
            depth = depth,
            limitPerNode = limitPerNode,
        )

    # MARK: Receiver

    @override
    def accept(self, tree: SampleTree, path: Path) -> Request:
        """
        Receive a request to ingest a tree for a path.

        The provided tree can contain multiple values for each node, and be of
        arbitrary depth.

        Components may choose to ignore parts of the tree due to access rights
        or other reasons.

        Args:
            tree: The tree to ingest.
            forPath: The path of the root node of the provided tree.

        Returns:
            A request handle, to optionally wait until the data is stored.

        Note:
            This function is not asynchronous because it is viewed as a request
            to store data. The data does not actually need to be stored when
            the function returns. To wait until the receive is completed, await
            the returned request.
        """
        return self._storage.accept(tree, path = self.path + path)

    # MARK: Storage

    @override
    def delete(
        self,
        path: Path | None = None,
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
    ) -> Request:
        """
        Delete data from the storage or node.

        If `path` is omitted, the delete is performed on this node.
        Otherwise, it is performed on the given child path.

        Parameters
        ----------
        path: Path
            The path of the node targeted for the delete.
        start: Timestamp | None
            The start of the interval to delete (exclusive,
            defaults to ``None``, meaning from the beginning of time).
        end: Timestamp | None
            The end of the interval to delete (inclusive,
            defaults to ``None``, meaning to the end of time).
        depth: int | None
            The number of levels to include for deletion below the given path.

        Returns
        -------
        Request
            A request that can be used to wait until completion.
        """
        if path is None:
            targetPath = self.path
        else:
            targetPath = self.path + path

        return self._storage.delete(
            path = targetPath,
            start = start,
            end = end,
            depth = depth,
        )

    # MARK: AnyStorageNode

    @override
    def setNull(self) -> Request:
        return self._storage.acceptValue(Value(None), path=self.path)

    @override
    def child(self, named: str) -> StorageNode:
        """
        Create a generic storage node for a child of this node.

        Args:
            named: The name of the child.

        Returns:
            The node representing the child.
        """
        return StorageNode(
            storage = self._storage,
            path = self.path + [named],
        )

    @override
    def deleteAtNode(self, start: Timestamp | None = None, end: Timestamp | None = None, depth: int | None = None) -> Request:
        return self._storage.delete(self.path, start, end, depth)

    # MARK: DataStorageNode

    @override
    def setData(self, value: bytes) -> Request:
        return self._storage.acceptValue(Value(value), path=self.path)

    @override
    async def dataValue(self) -> bytes | None:
        value = await self._storage.currentValue()
        if value is None:
            return None
        return value.dataValue

    # MARK: DoubleStorageNode

    @override
    def setDouble(self, value: float) -> Request:
        return self._storage.acceptValue(Value(value), path=self.path)

    @override
    async def doubleValue(self) -> float | None:
        value = await self._storage.currentValue()
        if value is None:
            return None
        return value.doubleValue

    # MARK: IntStorageNode

    @override
    def setInteger(self, value: int) -> Request:
        return self._storage.acceptValue(Value(value), path=self.path)

    @override
    async def integerValue(self) -> int | None:
        value = await self._storage.currentValue()
        if value is None:
            return None
        return value.intValue

    # MARK: PathStorageNode

    @override
    def setPath(self, value: Path) -> Request:
        return self._storage.acceptValue(Value(value), path=self.path)

    @override
    async def pathValue(self) -> Path | None:
        value = await self._storage.currentValue()
        if value is None:
            return None
        return value.pathValue

    # MARK: StringStorageNode

    @override
    def setString(self, value: str) -> Request:
        return self._storage.acceptValue(Value(value), path=self.path)

    @override
    async def stringValue(self) -> str | None:
        value = await self._storage.currentValue()
        if value is None:
            return None
        return value.stringValue
