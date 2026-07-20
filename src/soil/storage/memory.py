from typing import override

from ..components import Storage
from ..data import MutableSampleTree, Path, SampleTree, Timestamp
from ..requests import Request
from ..utils.actor import Actor, synchronized, queued


class InMemoryStorage(Actor, Storage):
    """
    A simple storage implementation that keeps all values in memory.

    Internally, the storage is organized in a tree, with an array of all samples for a path stored in each node.

    The database storage is not optimized for extreme performance.
    Each sample for a tree node is inserted separately, which may result in many array operations, even if batch inserts may be possible.
    The assumption is that mostly current samples will be received, which can be appended to the sorted internal array of history values.
    """

    root: MutableSampleTree
    """ The root node of the data tree, where all other data is stored """

    def __init__(self) -> None:
        Actor.__init__(self)
        """
        Create an in-memory storage.
        """
        self.root: MutableSampleTree = MutableSampleTree()

    @synchronized
    async def _accept(self, tree: SampleTree, path: Path):
        """
        Save the samples of a tree at a path.

        This function searches for the correct node in the tree, and inserts the tree.
        This includes inserting the provided values at the node, and then traversing the provided tree further, until all samples are stored.

        Parameters
        ----------
        tree: SampleTree
            The tree with the samples to store.
        path: Path
            The path of the tree.
        """
        self.root.findOrCreateNode(path).save(tree)

    @queued(default=SampleTree.empty())
    async def _getTree(self,
        path: Path,
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
        limitPerNode: int | None = None
    ) -> SampleTree:
        node = self.root.existingNode(path)
        if node is None:
            return SampleTree.empty()
        return node.tree(start, end, depth, limitPerNode)

    @synchronized
    async def _delete(self, path: Path, start: Timestamp | None, end: Timestamp | None, depth: int | None) -> None:
        """
        Delete data from the storage.

        The function searches for the correct node in the tree,
        and removes all applicable values from the historic samples at this node.

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
        """
        node = self.root.existingNode(path)
        if node is None:
            return
        node.delete(start, end, depth)

    # MARK: Storage

    @override
    def accept(self, tree: SampleTree, path: Path) -> Request:
        """
        Save the samples of a tree at a path.

        This function searches for the correct node in the tree, and inserts the tree.
        This includes inserting the provided values at the node, and then traversing the provided tree further, until all samples are stored.

        Parameters
        ----------
        tree: SampleTree
            The tree with the samples to store.
        path: Path
            The path of the tree.

        Returns
        -------
        Request
            The request, if the caller wants to wait for completion
        """
        return self._accept(tree, path)

    @override
    async def tree(self,
        path: Path,
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
        limitPerNode: int | None = None
    ) -> SampleTree:
        """
        Get the tree of a path within a date range, including sub-paths

        For each node, this function returns the samples in the specified date range.
        - Parameter path: The requested path
        - Parameter start: The start of the requested interval (exclusive, defaults to `nil`, meaning from end of time)
        - Parameter end: The end of the requested interval (inclusive, defaults to `nil`, meaning to beginning of time)
        - Parameter depth: The number of levels in the sub-tree to include
        - Parameter limitPerNode: The maximum number of values to return for each node in the tree (defaults to `nil`, e.g. no limit)
        - Returns: The values in the range, sorted from `start` to `end`, or by oldest first, if either is `nil`.
        If a limit is set, then the `limit` values counted in sort order are returned.
        """
        return await self._getTree(path, start, end, depth, limitPerNode)

    @override
    def delete(self, path: Path = Path(), start: Timestamp | None = None, end: Timestamp | None = None, depth: int | None = None) -> Request:
        """
        Delete data from the storage.

        The function searches for the correct node in the tree,
        and removes all applicable values from the historic samples at this node.
        - Parameter path: The path of the node targeted for the delete.
        - Parameter start: The start of the interval to delete (exclusive, defaults to `nil`, meaning from beginning of time)
        - Parameter end: The end of the interval to delete (inclusive, defaults to `nil`, meaning to end of time)
        - Parameter depth: The number of levels to include for deletion below the given path
        - Returns: A request that can be used to wait until completion
        """
        return self._delete(path, start, end, depth)


