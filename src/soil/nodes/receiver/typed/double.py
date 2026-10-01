
from ....data import Timestamp, Value
from ....requests import Request
from ...receiver.node import ReceiverNode


class DoubleReceiverNode(ReceiverNode):
    """
    A node that can receive doubles.
    """

    async def setDouble(self, value: float, timestamp: Timestamp | None = None) -> Request:
        """
        Ingest a double value.

        :param value: The double to store.
        :param timestamp: The timestamp associated with the value.
        """
        if timestamp is None:
            return super().set(Value(value))
        else:
            return super().set(Value(value), timestamp)
