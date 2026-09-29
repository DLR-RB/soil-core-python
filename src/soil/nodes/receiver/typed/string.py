
from ....data import Timestamp, Value
from ....requests import Request

from ...receiver import ReceiverNode


class StringReceiverNode(ReceiverNode):
    """
    A node that can receive strings.
    """

    def setString(self, value: str, timestamp: Timestamp | None = None) -> Request:
        """
        Ingest a string value.

        :param value: The string to store.
        :param timestamp: The timestamp associated with the value.
        """
        if timestamp is None:
            return super().set(Value(value))
        else:
            return super().set(Value(value), timestamp)
