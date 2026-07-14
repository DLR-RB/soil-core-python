from collections.abc import Awaitable
from abc import ABC, abstractmethod
from typing import Any, Generator


class Request(ABC, Awaitable[None]):
    """
    A request is a piece of asynchronous work that is in progress,
    which can optionally be awaited until completion.
    """

    @abstractmethod
    async def wait(self) -> None:
        """Wait until the request completes."""
        pass

    @abstractmethod
    def __await__(self) -> Generator[Any, Any, None]:
        """Wait until the request completes."""
        pass
