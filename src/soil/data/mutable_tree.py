
from typing import Callable, Dict, List, Protocol, Self, Sequence, TypeVar, override

from .immutable_tree import ImmutableSampleTree
from .path import Path
from .sample import Sample
from .sampletree import SampleTree
from .timestamp import Timestamp

class MutableSampleTree(SampleTree):

    def __init__(self, samples: List[Sample] | None = None, children: Dict[str, SampleTree] | None = None) -> None:
        self._samples: List[Sample] = samples if samples is not None else list()
        self._children: Dict[str, SampleTree] = children if children is not None else dict()

    @property
    @override
    def samples(self) -> List[Sample]:
        return self._samples

    @property
    @override
    def children(self) -> Dict[str, SampleTree]:
        return self._children # pyright: ignore[reportReturnType]

    @property
    @override
    def isEmpty(self) -> bool:
        return len(self._samples) == 0 and len(self._children) == 0

    @override
    @classmethod
    def create(cls, samples: List[Sample] | None = None, children: Dict[str, SampleTree] | None = None) -> Self:
        return cls(samples, children)

    def child(self, name: str) -> MutableSampleTree:
        """
        Select a child of this node with a given name.

        The child will be created, if it doesn't exist.
        This function is used for write operations.
        - Parameter name: The name of the child.
        - Returns: The node of the child.
        """
        child = self._children.get(name)
        if child is None:
            child = MutableSampleTree()
            self.children[name] = child
            return child
        if isinstance(child, MutableSampleTree):
            return child
        # Convert the child to a mutable tree
        newChild = MutableSampleTree(child.samples, child.children)
        self._children[name] = newChild
        return newChild

    def save(self, tree: SampleTree) -> None:
        """
        Save a tree at this node.

        Inserts all samples of the tree root, and recurses into the children to store the full tree.
        - Parameter tree: The tree to save for this node.
        """
        self.saveSamples(tree.samples)

        # Recurse into the tree to store all samples
        for name, subTree in tree.children.items():
            self.child(name).save(subTree)


    def saveSamples(self, samples: List[Sample]) -> None:
        """
        Save samples at this node.
        - Parameter samples: The samples to save for this node.
        """
        for sample in samples:
            self.insertSampleIntoHistory(sample.withTimeSet())

    def insertSampleIntoHistory(self, sample: Sample) -> None:
        """
        Insert a single sample into the history at this node.

        The sample is inserted at the correct index to keep the array sorted.
        - Parameter sample: The sample to insert
        """
        # We assume that most new values will be recent, so check the last value first
        if len(self.samples) != 0 and self.samples[-1] <= sample:
            self.samples.append(sample)
        else:
            # Do a binary search in the sorted array and insert in the right place
            insertIntoSorted(self.samples, sample)

    def tree(self,
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
        limitPerNode: int | None = None
    ) -> SampleTree:
        """
        Construct a tree in a provided interval with a maximum depth.
        - Parameter start: The start of the requested interval (exclusive, defaults to `nil`, meaning from end of time)
        - Parameter end: The end of the requested interval (inclusive, defaults to `nil`, meaning to beginning of time)
        - Parameter depth: The number of levels in the sub-tree to include
        - Parameter limitPerNode: The maximum number of values to return (defaults to `nil`, e.g. no limit)
        - Returns: The values in the range, sorted from `start` to `end`, or by oldest first, if either is `nil`.
        If a limit is set, then the `limit` values counted from `start` (or oldest) are returned.
        """
        samples = self.getSamples(start, end, limitPerNode)

        # Only return the value, if depth is reached
        if depth == 0:
            return ImmutableSampleTree(samples)

        newDepth = depth - 1 if depth is not None else None
        children: Dict[str, SampleTree] = dict()

        for name in self._children:
            child = self.child(name)
            childTree = child.tree(start, end, newDepth, limitPerNode)
            children[name] = childTree

        return ImmutableSampleTree(samples, children)

    def getSamples(self, start: Timestamp | None, end: Timestamp | None, limit: int | None) -> List[Sample]:
        """
        Provides the values in a given date range for a path, regardless of the value type.

        The sort order of the result is:
        - ascending, if `end = nil`
        - descending, if `end != nil` and `start = nil`
        - ascending, if `start < end`
        - descending, if `start > end`

        The `limit` is applied in sort order.

        - Parameter path: The requested path.
        - Parameter start: The start of the requested interval (exclusive, defaults to `nil`, meaning from beginning of time)
        - Parameter end: The end of the requested interval (inclusive, defaults to `nil`, meaning to end of time)
        - Parameter limit: The maximum number of values to return (defaults to `nil`, e.g. no limit)
        - Returns: The values in the range, sorted from `start` to `end`, or by oldest first, if either is `nil`. If a limit is set, then the `limit` values counted from `start` (or oldest) are returned.
        """
        if start is None:
            # No start provided, so use beginning of time
            if end is None:
                if limit is None:
                    # No start, end, or limit, so return the full history
                    return self._samples
                # Limit the full history, return in ascending order (already sorted correctly)
                return list(self._samples[:limit])
            # No start, but end provided: descending order, end inclusive
            endIndex = self._firstIndexAfter(end)
            return self.selectDescending(0, endIndex, limit)

        if end is None:
            # Start, but no end, so return in ascending order
            startIndex = self._firstIndexAfter(start)
            return self.selectAscending(startIndex, len(self._samples), limit)

        if start >= end:
            # Reverse order requested
            # This case needs to be treated differently, due to start being exclusive and end inclusive
            return self.selectDescendingInterval(end, start, limit)

        # Both start and end given in "correct" order, so return ascending
        startIndex = self._firstIndexAfter(start)
        endIndex = self._firstIndexAfter(end)
        return self.selectAscending(startIndex, endIndex, limit)

    def selectAscending(self, start: int, end: int, limit: int | None) -> List[Sample]:
        """
        Select all samples between two indices in storage (ascending) order, limited to a maximum count.
        - Parameter range: The range to select from `history`
        - Parameter limit: The optional limit, applied from the lower end of the range
        """
        # Move the end index if the range needs to be limited

        limitedEndIndex: int = end
        if limit is not None:
            limitedEndIndex = min(end, start + limit)
        return list(self._samples[start:limitedEndIndex])

    def selectDescendingInterval(self, start: Timestamp, end: Timestamp, limit: int | None) -> List[Sample]:
        """
        Select samples in the history in a date range in descending order, optionally limited to a maximum count.
        - Parameter start: The lower bound of the interval (inclusive)
        - Parameter end: The upper bound of the interval (exclusive)
        - Parameter limit: The optional count limit to apply, returning only the `limit` newest samples.
        """
        # The lower index of the subsequence is given by `start`
        # Start is inclusive, so we find the first index larger than or equal to `start`
        lowerIndex = partitioningIndex(self.samples, lambda a: a.time >= start)
        # The higher index is given by `end`, but exclusive.
        # Since we need the index after the last included element, we select the first index larger than or equal to `end`
        higherIndex = partitioningIndex(self.samples, lambda a: a.time >= end)
        # Now we select the subrange in descending order, with the limit applied from the higher index
        return self.selectDescending(lowerIndex, higherIndex, limit)

    def selectDescending(self, start: int, end: int, limit: int | None) -> List[Sample]:
        """
        Select all samples between two indices in reverse (descending) order, limited to a maximum count.

        - Note: The lower bound is inclusive, while the upper bound is exclusive.
        - Parameter range: The range to select from `history`
        - Parameter limit: The optional limit, applied from the upper end of the range
        """
        # Move the higher index if the range needs to be limited
        limitedLowerIndex = start
        if limit is not None:
            limitedLowerIndex = max(start, end - limit)
        # Reverse the subsequence, because the order is expected to be descending
        result = list(reversed(self._samples[limitedLowerIndex:end]))
        return result

    def _firstIndexAfter(self, date: Timestamp) -> int:
        """ Return the history index of the first element larger than the given date """
        # Find the first index in the array where the sample date is after the given date
        # If all values are smaller than or equal to the given date, then the end index is returned
        return partitioningIndex(self.samples, lambda a: a.time > date)

    def delete(self, start: Timestamp | None, end: Timestamp | None, depth: int | None) -> None:
        """
        Recursively delete all samples in an interval, with a maximum depth.
        - Parameter start: The start of the interval to delete (exclusive, defaults to `nil`, meaning from beginning of time)
        - Parameter end: The end of the interval to delete (inclusive, defaults to `nil`, meaning to end of time)
        - Parameter depth: The number of levels to include for deletion below this node
        """
        # Delete samples at this node
        self.deleteSamples(start, end)

        # Recurse to delete child samples
        newDepth = depth - 1 if depth is not None else None
        for name in self._children:
            self.child(name).delete(start, end, newDepth)

    def deleteSamples(self, start: Timestamp | None, end: Timestamp | None) -> None:
        """
        Delete all samples at the current node in the given range.

        The deletion works as follows:
        - If neither `start` nor `end` is provided, then all samples are deleted.
        - If only `end` is provided, then all samples with timestamps before `end` are removed (`end` is exclusive)
        - If only `start` is provided, then all values with timestamps after an including `start` are deleted (`start` is inclusive)
        - If both `start` and `end` are provided, then all values between `start` and `end` are deleted (`start` is inclusive, `end` is exclusive)
        - Parameter start: The start of the interval to delete (exclusive, defaults to `nil`, meaning from beginning of time)
        - Parameter end: The end of the interval to delete (inclusive, defaults to `nil`, meaning to end of time)
        """
        if start is None:
            # No start provided, so use beginning of time
            if end is None:
                # No end provided, so delete full history
                self._samples = list()
                return
            # No start, but end provided
            endIndex = self._firstIndexAfter(end)
            del self._samples[:endIndex]
            return

        if end is None:
            # Start, but no end, so delete all values after an including `start`
            startIndex = self._firstIndexAfter(start)
            del self._samples[startIndex:]
            return

        if start >= end:
            # Reverse order requested
            # This case needs to be treated differently, due to start being exclusive and end inclusive
            startIndex = partitioningIndex(self.samples, lambda a: a.time >= end)
            startIndex = partitioningIndex(self.samples, lambda a: a.time >= end)
            # The end index is given by `start`, but exclusive.
            # Since we need the index after the last included element, we select the first index larger than or equal to `start`
            endIndex = partitioningIndex(self.samples, lambda a: a.time >= start)
            del self._samples[startIndex:endIndex]
            return

        # Both start and end given in "correct" order
        startIndex = self._firstIndexAfter(start)
        endIndex = self._firstIndexAfter(end)
        # The start index is exclusive, and the end index is inclusive
        del self._samples[startIndex:endIndex]

    # MARK: Mutable Tree

    def findOrCreateNode(self, path: Path) -> MutableSampleTree:
        """
        Find an existing node, or create it in the tree.

        Used when inserting a subscription or exclusion.
        - Parameter path: The path to the node.
        - Returns: The final node corresponding to the path
        """
        node = self
        for component in path:
            node = node.child(component)
        return node

    def createChild(self, name: str) -> MutableSampleTree:
        child = MutableSampleTree()
        self._children[name] = child
        return child

    def add(self, child: MutableSampleTree, name: str) -> None:
        self._children[name] = child

    # MARK: Tree

    def existingNode(self, path: Path) -> MutableSampleTree | None:
        """
        Get a node for a path below the current node, if it exists.

        This function is used for read and delete operations, and does not create any new nodes.
        - Parameter path: The path to select within the tree.
        - Returns: The node at the path, if it exists.
        """
        current: MutableSampleTree = self
        for name in path:
            child = current.existingChild(name)
            if child is None:
                return None
            current = child
        return current

    def existingChild(self, name: str) -> MutableSampleTree | None:
        child = self._children.get(name)
        if child is None:
            return None
        if isinstance(child, MutableSampleTree):
            return child
        newChild = MutableSampleTree(child.samples, child.children)
        self._children[name] = newChild
        return newChild

    def existingNodes(self, path: Path) -> List[MutableSampleTree]:
        """
        Get all existing nodes in the tree on the way to a node corresponding to a path.
        - Note: Includes this node as the first element of the result
        - Parameter path: The path to the node.
        - Returns: All existing nodes along the path.
        """
        result: List[MutableSampleTree] = [self]
        last = self
        for component in path:
            child = last.existingChild(component)
            if child is None:
                break
            result.append(child)
            last = child
        return result

T = TypeVar("T")

def partitioningIndex(
    seq: Sequence[T],
    belongsInSecondPartition: Callable[[T], bool],
) -> int:
    """
    Returns the index of the first element for which
    belongsInSecondPartition(element) is True.

    Assumes seq is already partitioned according to the predicate.
    """
    lo, hi = 0, len(seq)

    while lo < hi:
        mid = (lo + hi) // 2
        if belongsInSecondPartition(seq[mid]):
            hi = mid
        else:
            lo = mid + 1
    return lo


class Comparable(Protocol):
    def __lt__(self, other: "Comparable", /) -> bool: ...

TT = TypeVar("TT", bound=Comparable)

def insertIntoSorted(lst: list[TT], value: TT) -> int:
    """
    Inserts value into the sorted list lst.

    Returns the index at which value was inserted.
    """
    i = partitioningIndex(lst, lambda x: not (x < value))
    lst.insert(i, value)
    return i