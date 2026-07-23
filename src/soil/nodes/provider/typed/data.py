
from ..node import ProviderNode


class DataProviderNode(ProviderNode):
    """
    A node that contains data.
    """

    async def getData(self) -> bytes | None:
        """
        Get the current data value, if it is data.

        If the current value is not data, then None is returned,
        even if a previous data value exists.

        :return: The current value.
        """
        value = await self.currentValue()

        if value is None:
            return None
        return value.dataValue
