
from ....data import Timestamp, Value
from ....requests import Request
from ...receiver.node import ReceiverNode


class DataReceiverNode(ReceiverNode):
    """
    A node that can receive data.
    """

    async def setData(self, value: bytes, timestamp: Timestamp | None = None) -> Request:
        """
        Ingest a data value.

        :param value: The data to store.
        :param timestamp: The timestamp associated with the value.
        """
        if timestamp is None:
            return super().set(Value(value))
        else:
            return super().set(Value(value), timestamp)
