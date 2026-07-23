
from ....data import Timestamp, Value

from ...receiver import ReceiverNode


class DataReceiverNode(ReceiverNode):
    """
    A node that can receive data.
    """

    async def setData(self, value: bytes, timestamp: Timestamp | None = None) -> None:
        """
        Ingest a data value.

        :param value: The data to store.
        :param timestamp: The timestamp associated with the value.
        """
        if timestamp is None:
            await super().set(Value(value))
        else:
            await super().set(Value(value), timestamp)
