
from ....data import Path, Timestamp, Value

from ...receiver import ReceiverNode


class PathReceiverNode(ReceiverNode):
    """
    A node that can receive paths.
    """

    async def setPath(self, value: Path, timestamp: Timestamp | None = None) -> None:
        """
        Ingest a path value.

        :param value: The path to store.
        :param timestamp: The timestamp associated with the value.
        """
        if timestamp is None:
            await super().set(Value(value))
        else:
            await super().set(Value(value), timestamp)
