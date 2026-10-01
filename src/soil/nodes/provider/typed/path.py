
from ....data import Path
from ..node import ProviderNode


class PathProviderNode(ProviderNode):
    """
    A node that contains paths.
    """

    async def gePath(self) -> Path | None:
        """
        Get the current path value, if it is a path.

        If the current value is not a path, then None is returned,
        even if a previous path value exists.

        :return: The current value.
        """
        value = await self.currentValue()

        if value is None:
            return None
        return value.pathValue
