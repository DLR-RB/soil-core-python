
from ..node import ProviderNode


class StringProviderNode(ProviderNode):
    """
    A node that contains strings.
    """

    async def getString(self) -> str | None:
        """
        Get the current string value, if it is a string.

        If the current value is not a string, then None is returned,
        even if a previous string value exists.

        :return: The current value.
        """
        value = await self.currentValue()

        if value is None:
            return None
        return value.stringValue
