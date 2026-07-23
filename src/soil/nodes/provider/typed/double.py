
from ..node import ProviderNode


class DoubleProviderNode(ProviderNode):
    """
    A node that contains doubles.
    """

    async def getDouble(self) -> float | None:
        """
        Get the current double value, if it is a double.

        If the current value is not a double, then None is returned,
        even if a previous double value exists.

        :return: The current value.
        """
        value = await self.currentValue()

        if value is None:
            return None
        return value.doubleValue
