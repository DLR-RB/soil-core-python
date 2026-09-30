
from ....data import Timestamp, Value
from ....requests import Request
from ...receiver.node import ReceiverNode


class IntReceiverNode(ReceiverNode):
    """
    A node that can receive integers.
    """

    async def setInteger(self, value: int, timestamp: Timestamp | None = None) -> Request:
        """
        Ingest a integer value.

        :param value: The integer to store.
        :param timestamp: The timestamp associated with the value.
        """
        if timestamp is None:
            return super().set(Value(value))
        else:
            return super().set(Value(value), timestamp)
