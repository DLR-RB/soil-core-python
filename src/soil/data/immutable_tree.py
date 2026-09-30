
from typing import override

from .sample import Sample
from .sampletree import SampleTree


class ImmutableSampleTree(SampleTree):
    """
    A path tree containing samples
    """

    def __init__(self, samples: list[Sample] | None = None, children: dict[str, SampleTree] | None = None):
        """
        Create a tree with samples and children.

        Parameters
        ----------
        samples: List[Sample]
            The data at the root node
        children: Dict[str, SampleTree]
            The child nodes of the tree root.
        Note: Defaults are None, because otherwise the same list or dict would be assigned to all objects
        """
        if samples is None:
            self._samples: list[Sample] = list()
        else:
            self._samples = samples
        if children is None:
            self._children: dict[str, SampleTree] = dict()
        else:
            self._children = children

    @property
    @override
    def samples(self) -> list[Sample]:
        return self._samples

    @property
    @override
    def children(self) -> dict[str, SampleTree]:
        return self._children

    @override
    @classmethod
    def create(cls, samples: list[Sample] | None = None, children: dict[str, SampleTree] | None = None) -> SampleTree:
        """
        Create a tree with samples and children.

        Parameters
        ----------
        samples: List[Sample]
            The data at the root node
        children: Dict[str, SampleTree]
            The child nodes of the tree root.
        Note: Defaults are None, because otherwise the same list or dict would be assigned to all objects
        """
        return ImmutableSampleTree(samples, children)

    @property
    @override
    def isEmpty(self) -> bool:
        if self.samples:
            return False
        for child in self.children.values():
            if not child.isEmpty:
                return False
        return True
