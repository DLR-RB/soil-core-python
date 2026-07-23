
from ..node import ProviderNode


class IntProviderNode(ProviderNode):
    """
    A node that contains integers.
    """

    async def getInteger(self) -> int | None:
        """
        Get the current integer value, if it is an integer.

        If the current value is not an integer, then None is returned,
        even if a previous integer value exists.

        :return: The current value.
        """
        value = await self.currentValue()

        if value is None:
            return None
        return value.intValue
