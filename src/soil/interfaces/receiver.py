from abc import ABC, abstractmethod
from typing import List

from ..data.immutable_sample_tree import ImmutableSampleTree
from ..data.path import Path
from ..data.sample import Sample
from ..data.sampletree import SampleTree
from ..data.timestamp import Timestamp
from ..data.value import Value
from ..requests.request import Request


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
    def receive(self, tree: SampleTree, path: Path = Path()) -> Request:
        """
        Receive a request to ingest a tree for a path.

        The provided tree can contain multiple values for each node, and be of arbitrary depth.

        Components may choose to ignore parts of the tree due to access rights or other reasons.

        Parameters:
            tree (SampleTree):
                The tree to ingest.
            path (Path):
                The path of the root node of the provided tree

        Returns:
            Request
                A request handle, to optionally wait until the data is ingested.

        Note: This function is not marked `async`, because it is viewed as a request to store data.
        The data does not actually need to be stored when the function returns, and should return as fast as possible.
        To wait until the receive is completed, await the returned request.
        """
        pass

    # MARK: Convenience methods

    def receiveValue(self, value: Value, path: Path = Path(), timestamp: Timestamp | None = None) -> Request:
        """
        Save a value for a path.
        - Parameter value: The value to store.
        - Parameter path: The path of the value.
        - Parameter timestamp: The timestamp associated with the value
        """
        sample = Sample(value, timestamp)
        return self.receiveSample(sample, path)

    def receiveSample(self, sample: Sample, path: Path = Path()) -> Request:
        """
        Save a timestamped value for a path

        Parameters:
            sample (Sample):
                The timestamped value to store.
            path (Path):
                The path of the value.
        """
        return self.receiveSamples([sample], path)

    def receiveSamples(self, samples: List[Sample], path: Path = Path()) -> Request:
        """
        Receive samples for a path.

        Components may choose to ignore samples due to access rights or other reasons.

        Parameters:
            samples (List[Sample]):
                The samples to store for the path.
            path (Path):
                The path associated with the samples
        Returns:
            Request:
                A request handle, to optionally wait until the data is stored.

        Note: This function is not marked `async`, because it is viewed as a request to store data.
        The data does not actually need to be stored when the function returns, and should return as fast as possible.
        To wait until the receive is completed, await the returned request.
        """
        return self.receive(ImmutableSampleTree(samples), path)
