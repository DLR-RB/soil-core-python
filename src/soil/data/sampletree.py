from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol, Self, TypeVar

from .convertible import SampleTreeConvertible, ValueConvertible
from .path import Path
from .sample import Sample
from .timestamp import Timestamp


class SampleTree:
    """
    A tree structure containing samples.

    Each node stores a list of samples and children indexed by path component.
    """

    def __init__(self, samples: list[Sample] | None = None, children: dict[str, SampleTree] | None = None) -> None:
        """
        Create a tree with samples and children.

        Parameters
        ----------
        samples:
            The samples at the root node.
        children:
            The child nodes of the tree, indexed by path component.

        Note: Defaults are None, because otherwise the same list or dict would be assigned to all objects.
        """
        self._samples: list[Sample] = samples if samples is not None else list()
        self._children: dict[str, SampleTree] = children if children is not None else dict()

    @property
    def samples(self) -> list[Sample]:
        """
        The samples at this tree node.
        """
        return self._samples

    @property
    def children(self) -> dict[str, SampleTree]:
        """
        The child nodes of the tree, indexed by path component.
        """
        return self._children

    @classmethod
    def create(cls, samples: list[Sample] | None = None, children: dict[str, SampleTree] | None = None) -> Self:
        """
        Create a tree with samples and children.
        """
        return cls(samples, children)

    @property
    def isEmpty(self) -> bool:
        """
        Indicate whether the tree contains any samples.

        Child nodes are included in the check.

        Returns
        -------
        bool
            True if neither this node nor any descendant node
            contains samples.
        """
        if self._samples:
            return False
        return all(child.isEmpty for child in self._children.values())


    @classmethod
    def empty(cls) -> Self:
        """
        Create an empty tree.
        """
        return cls.create()

    @classmethod
    def ofSample(cls, sample: Sample, children: dict[str, SampleTree] | None = None) -> Self:
        """
        Create a tree with a sample at the root.

        Parameters
        ----------
        sample:
            The sample at the root.
        children:
            Child nodes indexed by path component.

        Returns
        -------
        Self
            A tree containing the provided sample.
        """
        return cls.create([sample], children)

    @classmethod
    def ofValue(cls, value: ValueConvertible, timestamp: Timestamp | None = None, children: dict[str, SampleTree] | None = None) -> Self:
        """
        Create a tree with a value at the root.

        Parameters
        ----------
        value:
            The value at the root.
        timestamp:
            Optional timestamp associated with the value.
        children:
            Child nodes indexed by path component.

        Returns
        -------
        Self
            A tree containing a single sample at the root.
        """
        return cls.ofSample(Sample(value, timestamp), children)
    
    @property
    def newestSample(self) -> Sample | None:
        """
        The most recent sample at this node.

        Only samples at this node are considered,
        not those of descendant nodes.

        Returns
        -------
        Sample | None
            The sample with the latest timestamp, or None
            if no samples exist at this node.
        """
        if not self.samples:
            return None
        return max(self.samples)

    @property
    def currentSample(self) -> Sample | None:
        """
        The sample whose timestamp is closest to the current time
        without being in the future.

        Samples without timestamps are treated as current and
        returned immediately.

        Returns
        -------
        Sample | None
            The best matching sample.
        """
        now = Timestamp.current()
        result: Sample | None = None

        for sample in self.samples:
            timestamp = sample.timestamp

            if timestamp is None:
                return sample

            if timestamp > now:
                continue

            if (
                result is not None
                and result.timestamp is not None
                and result.timestamp > timestamp
            ):
                continue

            result = sample

        return result

    
    @property
    def numberOfNodesWithSamples(self) -> int:
        """
        The number of nodes in the subtree (including this node)
        that contain at least one sample.

        Returns
        -------
        int
            The count of nodes holding samples.
        """
        count = 1 if self.samples else 0
        for child in self.children.values():
            count += child.numberOfNodesWithSamples
        return count


    @property
    def totalNumberOfSamples(self) -> int:
        """
        The total number of samples across this node
        and all descendant nodes.

        Returns
        -------
        int
            The cumulative sample count of the subtree.
        """
        total = len(self.samples)
        for child in self.children.values():
            total += child.totalNumberOfSamples
        return total

    
    @property
    def currentValue(self) -> ValueConvertible | None:
        """
        The value of the current sample.

        Returns
        -------
        ValueConvertible | None
            The value associated with ``currentSample``.
        """
        sample = self.currentSample
        return None if sample is None else sample.value


    def containedTree(self) -> tuple[Path, SampleTree]:
        """
        Find the first meaningful subtree.

        Traverses down chains of single-child nodes until a node
        containing samples or multiple children is encountered.

        Returns
        -------
        Tuple[Path, SampleTree]
            The path to the subtree and the subtree itself.
        """
        path = Path()
        current: SampleTree = self

        while (
            not current.samples
            and len(current.children) == 1
        ):
            name, child = next(iter(current.children.items()))
            path.append(name)
            current = child

        return path, current

    def containedTreeAtPath(self, path: Path) -> tuple[Path, SampleTree]:
        """
        Find the first meaningful subtree, and combine it with a given path.

        Traverses down chains of single-child nodes until a node
        containing samples or multiple children is encountered.

        Returns
        -------
        Tuple[Path, SampleTree]
            The full path to the subtree and the subtree itself.
        """
        subPath, tree = self.containedTree()
        return path.appending(subPath), tree

    def isEqualTo(self, other: SampleTree) -> bool:
        """
        Compare two trees recursively.

        Parameters
        ----------
        other:
            The tree to compare against.

        Returns
        -------
        bool
            True if the trees contain identical samples and
            child structures.
        """
        if self.samples != other.samples:
            return False

        if len(self.children) != len(other.children):
            return False

        for name, child in self.children.items():
            otherChild = other.children.get(name)

            if otherChild is None:
                return False

            if not child.isEqualTo(otherChild):
                return False

        return True

    def describe(
        self,
        indentLevel: int = 0,
        indent: str = "  ",
    ) -> list[str]:
        """
        Produce a multi-line tree description.

        Parameters
        ----------
        indentLevel:
            Initial indentation level.
        indent:
            Indentation string.

        Returns
        -------
        list[str]
            Lines describing the tree.
        """
        baseIndent = indent * indentLevel
        result: list[str] = []

        if self.samples:
            sampleIndent = baseIndent + indent

            result.append(baseIndent + "samples:")

            for sample in self.samples:
                result.append(sampleIndent + str(sample))

        if self.children:
            childIndent = baseIndent + indent

            result.append(baseIndent + "children:")

            for name, child in self.children.items():
                result.append(f"{childIndent}{name}:")
                result.extend(
                    child.describe(
                        indentLevel=indentLevel + 2,
                        indent=indent,
                    )
                )

        return result

    def __str__(self) -> str:
        """
        Return a human-readable description of the tree.
        """
        return "\n".join(self.describe())

    def __eq__(self, other: object) -> bool:
        """
        Compare two sample trees.
        """
        if not isinstance(other, SampleTree):
            return False

        return self.isEqualTo(other)


    def insert(self, samples: list[Sample], path: Path) -> None:
        """
        Insert samples into the tree.
        - Parameter samples: The samples to add
        - Parameter path: The path within this tree where the samples are added.
        - Note: The samples are appended to existing samples without sorting.
        """
        self.findOrCreateNode(path).samples.extend(samples)

    def mergeAtPath(self, tree: SampleTree | SampleTreeConvertible, path: Path) -> None:
        """
        Insert a tree into this tree.
        - Parameter tree: The tree to add
        - Parameter path: The path within this tree where the tree is added.
        - Note: The samples are appended to existing samples without sorting.
        """
        self.findOrCreateNode(path).merge(tree)

    def merge(self, tree: SampleTree | SampleTreeConvertible) -> None:
        """
        Insert a tree into this tree.
        - Parameter tree: The tree to add
        - Note: The samples are appended to existing samples without sorting.
        """

        tree = asTree(tree)
        self.samples.extend(tree.samples)
        for name, child in tree.children.items():
            node = self.child(name)
            node.merge(child)

    def child(self, name: str) -> SampleTree:
        """
        Select a child of this node with a given name.

        The child will be created, if it doesn't exist.
        This function is used for write operations.
        - Parameter name: The name of the child.
        - Returns: The node of the child.
        """
        child = self._children.get(name)
        if child is None:
            child = SampleTree()
            self._children[name] = child
        return child

    def childWithValue(self, name: str, value: ValueConvertible) -> SampleTree:
        """
        Select a child of this node with a given name, and insert a value as a new sample.

        The child will be created, if it doesn't exist.
        This function is used for write operations.

        - Parameter name: The name of the child.
        - Parameter value: The value to insert into the child (accepted as ValueConvertible, stored as Value).
        - Returns: The node of the child.
        """
        child = self.child(name)
        child.insertSampleIntoHistory(Sample(value, Timestamp.current()))
        return child

    def save(self, tree: SampleTree | SampleTreeConvertible) -> None:
        """
        Save a tree at this node.

        Inserts all samples of the tree root, and recurses into the children to store the full tree.
        - Parameter tree: The tree to save for this node.
        """

        tree = asTree(tree)
        self.saveSamples(tree.samples)

        # Recurse into the tree to store all samples
        for name, subTree in tree.children.items():
            self.child(name).save(subTree)

    def saveSamples(self, samples: list[Sample]) -> None:
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

        # Only return the samples, if depth is reached
        if depth == 0:
            return SampleTree(samples)

        newDepth = depth - 1 if depth is not None else None
        children: dict[str, SampleTree] = dict()

        for name, child in self._children.items():
            children[name] = child.tree(start, end, newDepth, limitPerNode)

        return SampleTree(samples, children)

    def getSamples(self, start: Timestamp | None, end: Timestamp | None, limit: int | None) -> list[Sample]:
        """
        Provides the values in a given date range for a path, regardless of the value type.

        The sort order of the result is:
        - ascending, if `end = nil`
        - descending, if `end != nil` and `start = nil`
        - ascending, if `start < end`
        - descending, if `start > end`

        The `limit` is applied in sort order.

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
                    # Copy the list, so that callers cannot mutate the stored history
                    return list(self._samples)
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

    def selectAscending(self, start: int, end: int, limit: int | None) -> list[Sample]:
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

    def selectDescendingInterval(self, start: Timestamp, end: Timestamp, limit: int | None) -> list[Sample]:
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

    def selectDescending(self, start: int, end: int, limit: int | None) -> list[Sample]:
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
        return list(reversed(self._samples[limitedLowerIndex:end]))

    def _firstIndexAfter(self, date: Timestamp) -> int:
        """ Return the history index of the first element larger than the given date """
        # Find the first index in the array where the sample date is after the given date
        # If all values are smaller than or equal to the given date, then the end index is returned
        return partitioningIndex(self.samples, lambda a: a.time > date)

    # MARK: Deletion

    def delete(self, start: Timestamp | None, end: Timestamp | None, depth: int | None) -> None:
        """
        Recursively delete all samples in an interval, with a maximum depth.
        - Parameter start: The start of the interval to delete (exclusive, defaults to `nil`, meaning from beginning of time)
        - Parameter end: The end of the interval to delete (inclusive, defaults to `nil`, meaning to end of time)
        - Parameter depth: The number of levels to include for deletion below this node
        """
        # Delete samples at this node
        self.deleteSamples(start, end)

        if depth == 0:
            return

        # Recurse to delete child samples
        newDepth = depth - 1 if depth is not None else None
        for child in self._children.values():
            child.delete(start, end, newDepth)

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
            # The lower index is given by `end`
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


    def findOrCreateNode(self, path: Path) -> SampleTree:
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

    def createChild(self, name: str) -> SampleTree:
        """
        Create a new empty child node with the given name.

        Unlike ``child``, this method does not check whether
        a child with that name already exists and will overwrite it.

        Parameters
        ----------
        name:
            The path component name for the new child node.

        Returns
        -------
        SampleTree
            The newly created child node.
        """
        child = SampleTree()
        self._children[name] = child
        return child

    def add(self, child: SampleTree, name: str) -> None:
        """
        Attach an existing tree as a child of this node.

        If a child with the same name already exists, it is replaced.

        Parameters
        ----------
        child:
            The tree to attach.
        name:
            The path component name under which the tree is stored.
        """
        self._children[name] = child

    def existingNode(self, path: Path) -> SampleTree | None:
        """
        Get a node for a path below the current node, if it exists.

        This function is used for read and delete operations, and does not create any new nodes.
        - Parameter path: The path to select within the tree.
        - Returns: The node at the path, if it exists.
        """
        current: SampleTree = self
        for name in path:
            child = current.existingChild(name)
            if child is None:
                return None
            current = child
        return current

    def existingChild(self, name: str) -> SampleTree | None:
        """
        Select a child of this node by name without creating it.

        This is the read-only counterpart to ``child``.

        Parameters
        ----------
        name:
            The path component name to look up.

        Returns
        -------
        SampleTree | None
            The child node, or None if no child with that name exists.
        """
        return self._children.get(name)

    def existingNodes(self, path: Path) -> list[SampleTree]:
        """
        Get all existing nodes in the tree on the way to a node corresponding to a path.
        - Note: Includes this node as the first element of the result
        - Parameter path: The path to the node.
        - Returns: All existing nodes along the path.
        """
        result: list[SampleTree] = [self]
        last = self
        for component in path:
            child = last.existingChild(component)
            if child is None:
                break
            result.append(child)
            last = child
        return result


def asTree(tree: SampleTree | SampleTreeConvertible) -> SampleTree:
    """
    Convert a SampleTreeConvertible into a SampleTree.

    SampleTrees are passed through unchanged.
    Use this at the entry point of functions that accept both.
    """
    if isinstance(tree, SampleTree):
        return tree
    return tree.toTree()

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
    def __lt__(self, other: Comparable, /) -> bool: ...


TT = TypeVar("TT", bound=Comparable)

def insertIntoSorted(lst: list[TT], value: TT) -> int:
    """
    Inserts value into the sorted list lst.

    Returns the index at which value was inserted.
    """
    i = partitioningIndex(lst, lambda x: not (x < value))
    lst.insert(i, value)
    return i