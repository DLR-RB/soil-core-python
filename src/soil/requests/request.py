from abc import ABC, abstractmethod
from asyncio import Future


class Request(ABC):
    """
    A request is a piece of asynchronous work that is in progress,
    which can optionally be awaited until completion.
    """

    @abstractmethod
    async def wait(self) -> None:
        """Wait until the request completes."""
        pass


class AsyncRequest(Request):
    """A request wrapping an asyncio.Future."""

    def __init__(self, future: Future[None]):
        self._future = future

    async def wait(self) -> None:
        await self._future


class CompletedRequest(Request):
    """ A request that is already completed """

    def __init__(self) -> None:
        pass

    async def wait(self) -> None:
        pass