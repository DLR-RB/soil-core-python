
from ....data import Timestamp, Value

from ...receiver import ReceiverNode


class IntReceiverNode(ReceiverNode):
    """
    A node that can receive integers.
    """

    async def setInteger(self, value: int, timestamp: Timestamp | None = None) -> None:
        """
        Ingest a integer value.

        :param value: The integer to store.
        :param timestamp: The timestamp associated with the value.
        """
        if timestamp is None:
            await super().set(Value(value))
        else:
            await super().set(Value(value), timestamp)
