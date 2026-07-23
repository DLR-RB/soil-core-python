
from ....data import Timestamp, Value

from ...receiver import ReceiverNode


class DoubleReceiverNode(ReceiverNode):
    """
    A node that can receive doubles.
    """

    async def setDouble(self, value: float, timestamp: Timestamp | None = None) -> None:
        """
        Ingest a double value.

        :param value: The double to store.
        :param timestamp: The timestamp associated with the value.
        """
        if timestamp is None:
            await super().set(Value(value))
        else:
            await super().set(Value(value), timestamp)
