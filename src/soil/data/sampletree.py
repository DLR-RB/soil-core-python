from abc import ABC, abstractmethod
from typing import Dict, List, Self, Tuple

from .path import Path
from .sample import Sample
from .timestamp import Timestamp
from .value import Value


class SampleTree(ABC):

    @property
    @abstractmethod
    def samples(self) -> List[Sample]:
        """
        The samples at this tree node.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def children(self) -> Dict[str, 'SampleTree']:
        """
        The child nodes of the tree, indexed by path component.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def create(cls, samples: List[Sample] | None = None, children: Dict[str, SampleTree] | None = None) -> Self:
        """

        Note: This function acts as a required constructor for all subclasses
        """
        pass

    @property
    @abstractmethod
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
        pass

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


    @classmethod
    def empty(cls) -> 'SampleTree':
        """
        Create an empty tree.

        Returns
        -------
        Self
            An empty tree containing no samples and no children.
        """
        return cls.create()

    @classmethod
    def ofSample(cls, sample: Sample, children: Dict[str, SampleTree] | None = None) -> Self:
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
    def ofValue(cls, value: Value, timestamp: Timestamp | None = None, children: Dict[str, SampleTree] | None = None) -> Self:
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

        Returns
        -------
        Sample | None
            The sample with the latest timestamp.
            Future timestamps are included.
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
    def currentValue(self) -> Value | None:
        """
        The value of the current sample.

        Returns
        -------
        Value | None
            The value associated with ``currentSample``.
        """
        sample = self.currentSample
        return None if sample is None else sample.value

    @property
    def numberOfNodesWithSamples(self) -> int:
        """
        Count nodes that contain samples.

        Returns
        -------
        int
            Number of nodes in the tree containing one or more
            samples.
        """
        count = 1 if self.samples else 0

        for child in self.children.values():
            count += child.numberOfNodesWithSamples

        return count

    @property
    def totalNumberOfSamples(self) -> int:
        """
        Count all samples in the tree.

        Returns
        -------
        int
            Total sample count across all nodes.
        """
        total = len(self.samples)

        for child in self.children.values():
            total += child.totalNumberOfSamples

        return total

    def containedTree(self) -> Tuple[Path, 'SampleTree']:
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

    def containedTreeAtPath(self, path: Path) -> Tuple[Path, 'SampleTree']:
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
