
from typing import Dict, List, override

from .sample import Sample
from .sampletree import SampleTree


class ImmutableSampleTree(SampleTree):
    """
    A path tree containing samples
    """

    def __init__(self, samples: List[Sample] | None = None, children: Dict[str, SampleTree] | None = None):
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
            self._samples: List[Sample] = list()
        else:
            self._samples = samples
        if children is None:
            self._children: Dict[str, SampleTree] = dict()
        else:
            self._children = children

    @property
    @override
    def samples(self) -> List[Sample]:
        return self._samples

    @property
    @override
    def children(self) -> Dict[str, SampleTree]:
        return self._children

    @override
    @classmethod
    def create(cls, samples: List[Sample] | None = None, children: Dict[str, SampleTree] | None = None) -> SampleTree:
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
