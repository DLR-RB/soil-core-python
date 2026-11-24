from abc import ABC, abstractmethod

from ..data import Path, Sample, SampleTree, Timestamp, Value


class Provider(ABC):
    """
    A component that can provide values.

    The term `provider` was chosen to emphasize the fact that this type of component does not
    send values by itself, but makes data available when requested.

    - Note: In other contexts, a provider may also be called a data source, sender, producer, publisher, transmitter, or writer.
    """

    @abstractmethod
    async def tree(self, path: Path = Path(), start: Timestamp | None = None, end: Timestamp | None = None, depth: int | None = None, limitPerNode: int | None = None) -> SampleTree:
        """
        Read a data tree for a given path within a given interval.

        This is the singular function to serve all data retrieval needs.

        The sort order of the result is:
        - ascending, if `end = nil`
        - descending, if `end != nil` and `start = nil`
        - ascending, if `start < end`
        - descending, if `start > end`

        The `limitPerNode` is applied in sort order.

        Parameters
        ----------
        path: Path
            The requested path (defaults to empty path, meaning the root)
        start: Timestamp | None
            The start of the requested interval (exclusive, defaults to `nil`, meaning from beginning of time)
        end: Timestamp | None
            The end of the requested interval (inclusive, defaults to `nil`, meaning to end of time)
        depth: int | None
            The number of levels below the path to include in the result
        limitPerNode: int | None
            The maximum number of values to return for each node of the tree (defaults to `nil`, e.g. no limit)

        Returns
        -------
        SampleTree
            The tree with the given depth, limited to the maximum count per node, for the requested interval.

        - Note: This function is `async`, because providing the data may take some time.
        It could be retrieved over a network, from an otherwise slow database, or from other components.
        """

    async def treeAtTime(self, path: Path = Path(), time: Timestamp = Timestamp.current(), depth: int | None = None) -> SampleTree:
        """
        Get the values of a path at a specific point in time, including sub-paths

        For each node, this function returns the most recent sample that is before or at the specified date.

        Parameters
        ----------
        path: Path
            The requested path.
        time: Timestamp
            The point in time which is requested (inclusive, `nil` indicates the current time).
        depth: int | None
            The number of levels in the sub-tree to include

        Returns
        -------
        The sample containing the current values of the requested sub-tree.
        """
        return await self.tree(path, None, time, depth, 1)

    async def samples(self,
        path: Path = Path(),
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        limit: int | None = None
    ) -> list[Sample]:
        """
        Provides the values in a given date range for a path, regardless of the value type.

        The sort order of the result is:
        - ascending, if `end = nil`
        - descending, if `end != nil` and `start = nil`
        - ascending, if `start < end`
        - descending, if `start > end`

        The `limit` is applied in sort order.

        Parameters
        ----------
        path: Path
            The requested path.
        start: Timestamp | None
            The start of the requested interval (exclusive, defaults to `nil`, meaning from beginning of time)
        end: Timestamp | None
            The end of the requested interval (inclusive, defaults to `nil`, meaning to end of time)
        limit: int | None
            The maximum number of values to return (defaults to `nil`, e.g. no limit)

        Returns
        -------
        List[Sample]
            The values in the range, limit to the maximum count
        """
        return (await self.tree(path, start, end, 0, limit)).samples

    async def sample(self, path: Path = Path(), time: Timestamp | None = None) -> Sample | None:
        """
        Get the value for a path at a specific point in time.

        Parameters
        ----------
        path: Path
            The requested path
        time: Timestamp
            The point in time for which the value is requested (inclusive, `nil` indicates the most recent sample)

        Returns
        -------
        Sample
            If present: The most recent value for the path where the timestamp is before the provided date.
        """
        samples = (await self.tree(path, None, time, depth = 0, limitPerNode = 1)).samples
        if len(samples) == 0:
            return None
        return samples[0]

    async def currentValue(self, path: Path = Path()) -> Value | None:
        """
        Get the current value for a path.
        Parameters
        ----------
        path: Path
            The requested path

        Returns
        -------
        Value
            The most recent timestamped value for the path, if present
        """
        sample = await self.currentSample(path)
        return sample.value if sample is not None else None

    async def currentSample(self, path: Path = Path()) -> Sample | None:
        """
        Get the current value for a path.
        - Parameter path: The requested path

        Returns
        -------
        Sample
            The most recent timestamped value for the path, if present
        """
        return await self.sample(path, time = Timestamp.current())

    async def currentTree(self, path: Path = Path(), depth: int | None = None) -> SampleTree:
        """
        Get the current values of a path, including sub-paths up to a given depth

        Parameters
        ----------
        path: Path
            The requested path
        depth: int | None
            The number of levels in the sub-tree to include

        Returns
        -------
        SampleTree
            The sample containing the current values of the requested sub-tree.
        """
        return await self.tree(path, start = None, end = Timestamp.current(), depth = depth, limitPerNode = 1)
