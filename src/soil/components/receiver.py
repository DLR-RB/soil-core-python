from abc import ABC, abstractmethod
from typing import List

from ..data import ImmutableSampleTree, Path, Sample, SampleTree, Timestamp, Value
from ..requests import Request



class Receiver(ABC):
    """
    A component that can receive values.

    The name `Receiver` was chosen to indicate that data from other components can be received, without necessarily being requested.

    Similar, but rejected terms include:
    - Sink: Vaguely implies that data is consumed, but it may also be retransmitted or stored.
    - Consumer: Implies that data is processed, but it may just be stored or forwarded
    - Client: Ambiguous, a client may have much functionality, including sending data
    - Subscriber: Implies that the component chooses which data to receive
    - Listener: Also suggests that the component is actively looking for data
    """

    @abstractmethod
    def accept(self, tree: SampleTree, path: Path) -> Request:
        """
        Receive a request to ingest a tree for a path.

        The provided tree can contain multiple values for each node, and be of arbitrary depth.

        Components may choose to ignore parts of the tree due to access rights or other reasons.

        Parameters
        ----------
        tree: SampleTree
            The tree to ingest
        path: Path
            The path of the root node of the provided tree

        Returns
        -------
        Request
            A request handle, to optionally wait until the data is ingested.

        - Note: This function is not marked `async`, because it is viewed as a request to store data.
        The data does not actually need to be stored when the function returns, and should return as fast as possible.
        To wait until the receive is completed, await the returned request.
        """
        pass

    def acceptRootTree(self, tree: SampleTree) -> Request:
        """
        Receive a tree for the root path.

        Parameters
        ----------
        tree: SampleTree
            The tree to store.

        Returns
        -------
        Request
            A request to wait for completion.
        """
        return self.accept(tree, Path())

    def acceptValue(self, value: Value, path: Path = Path(), timestamp: Timestamp | None = None) -> Request:
        """
        Save a value for a path.

        Parameters
        ----------
        value: Value
            The value to store.
        path: Path
            The path of the value.
        timestamp: Timestamp
            The timestamp associated with the value

        Returns
        -------
        Request
            A request to wait for completion.
        """
        return self.acceptSample(Sample(value, timestamp), path)

    def acceptSample(self, sample: Sample, path: Path = Path()) -> Request:
        """
        Save a timestamped value for a path
        - Parameter sample: The timestamped value to store.
        - Parameter path: The path of the value.

        Returns
        -------
        Request
            A request to wait for completion.
        """
        return self.acceptSamples([sample], path)

    def acceptSamples(self, samples: List[Sample], path: Path = Path()) -> Request:
        """
        Receive samples for a path.

        Components may choose to ignore samples due to access rights or other reasons.
        - Note: This function is not marked `async`, because it is viewed as a request to store data.
        The data does not actually need to be stored when the function returns, and should return as fast as possible.
        To wait until the receive is completed, await the returned request.

        Parameters
        ----------
        samples: List[Sample]
            The samples to store for the path.
        path: Path
            The path associated with the samples

        Returns
        -------
        Request
            A request handle, to optionally wait until the data is stored.
        """
        tree = ImmutableSampleTree(samples)
        return self.accept(tree, path)

