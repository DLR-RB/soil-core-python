
from ....data import Path, Timestamp, Value
from ....requests import Request

from ...receiver import ReceiverNode


class PathReceiverNode(ReceiverNode):
    """
    A node that can receive paths.
    """

    def setPath(self, value: Path, timestamp: Timestamp | None = None) -> Request:
        """
        Ingest a path value.

        :param value: The path to store.
        :param timestamp: The timestamp associated with the value.
        """
        if timestamp is None:
            return super().set(Value(value))
        else:
            return super().set(Value(value), timestamp)
