from abc import ABC, abstractmethod
from collections.abc import Awaitable, Generator
from typing import Any


class Request(ABC, Awaitable[None]):
    """
    A request is a piece of asynchronous work that is in progress,
    which can optionally be awaited until completion.
    """

    @abstractmethod
    async def wait(self) -> None:
        """Wait until the request completes."""

    @abstractmethod
    def __await__(self) -> Generator[Any, Any, None]:
        """Wait until the request completes."""
