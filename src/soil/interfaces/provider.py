from abc import ABC, abstractmethod
from typing import List

from soil.data.sample import Sample

from ..data import Path, SampleTree, Timestamp, Value

"""
 A component that can provide values.

 The term `provider` was chosen to emphasize the fact that this type of component does not
 send values by itself, but makes data available when requested.

 - Note: In other contexts, a provider may also be called a data source, sender, producer, publisher, transmitter, or writer.
"""
class Provider(ABC):

    @abstractmethod
    async def tree(self, path: Path, start: Timestamp | None, end: Timestamp | None, depth: int | None, limitPerNode: int | None) -> SampleTree:
        """
        Read a data tree for a given path within a given interval.

        This is the singular function to serve all data retrieval needs.

        The sort order of the result is:
        - ascending, if `end = nil`
        - descending, if `end != nil` and `start = nil`
        - ascending, if `start < end`
        - descending, if `start > end`

        The `limitPerNode` is applied in sort order.

        - Parameter path: The requested path.
        - Parameter start: The start of the requested interval (exclusive, defaults to `nil`, meaning from beginning of time)
        - Parameter end: The end of the requested interval (inclusive, defaults to `nil`, meaning to end of time)
        - Parameter depth: The number of levels below the path to include in the result
        - Parameter limitPerNode: The maximum number of values to return for each node of the tree (defaults to `nil`, e.g. no limit)
        - Returns: The tree with the given depth, limited to the maximum count per node, for the requested interval.
        - Note: This function is `async`, because providing the data may take some time.
        It could be retrieved over a network, from an otherwise slow database, or from other components.
        """
        pass

    async def treeAtTime(self, path: Path, time: Timestamp, depth: int | None = None) -> SampleTree:
        """
        Get the values of a path at a specific point in time, including sub-paths

        For each node, this function returns the most recent sample that is before or at the specified date.
        - Parameter path: The requested path
        - Parameter date: The point in time which is requested (inclusive, `nil` indicates the current time).
        - Parameter depth: The number of levels in the sub-tree to include
        - Returns: The sample containing the current values of the requested sub-tree.
        """
        return await self.tree(path, start = None, end = time, depth = depth, limitPerNode = 1)

    async def samples(self, path: Path = Path(), start: Timestamp | None = None, end: Timestamp | None = None, limit: int | None = None) -> List[Sample]:
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
        - Returns: The values in the range, limit to the maximum count
        """
        tree = await self.tree(path, start, end, depth = 0, limitPerNode = limit)
        return tree.samples

    async def sample(self, path: Path, beforeOrAt: Timestamp) -> Sample | None:
        """
        Get the value for a path at a specific point in time.
        - Parameter path: The requested path
        - Parameter date: The point in time for which the value is requested (inclusive, `nil` indicates the most recent sample)
        - Returns: If present: The most recent value for the path where the timestamp is before the provided date.
        """
        samples = await self.samples(path, start = None, end = beforeOrAt, limit = 1)
        return samples[0] if samples else None

    async def currentSample(self, path: Path = Path()) -> Sample | None:
        """
        Get the current value for a path.
        - Parameter path: The requested path
        - Returns: The most recent timestamped value for the path, if present
        """
        return await self.sample(path, beforeOrAt = Timestamp.current())

    async def currentValue(self, path: Path = Path()) -> Value | None:
        """
        Get the current value for a path.
        - Parameter path: The requested path
        - Returns: The most recent timestamped value for the path, if present
        """
        sample = await self.currentSample(path)
        return sample.value if sample is not None else None

    async def currentTree(self, *, path: Path = Path(), depth: int | None) -> SampleTree:
        """
        Get the current values of a path, including sub-paths up to a given depth
        - Parameter path: The requested path
        - Parameter depth: The number of levels in the sub-tree to include
        - Returns: The sample containing the current values of the requested sub-tree.
        """
        return await self.tree(path, start = None, end = Timestamp.current(), depth = depth, limitPerNode = 1)
