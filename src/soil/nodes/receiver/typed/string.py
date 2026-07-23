
from ....data import Timestamp, Value

from ...receiver import ReceiverNode


class StringReceiverNode(ReceiverNode):
    """
    A node that can receive strings.
    """

    async def setString(self, value: str, timestamp: Timestamp | None = None) -> None:
        """
        Ingest a string value.

        :param value: The string to store.
        :param timestamp: The timestamp associated with the value.
        """
        if timestamp is None:
            await super().set(Value(value))
        else:
            await super().set(Value(value), timestamp)
