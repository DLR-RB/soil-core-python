from asyncio import CancelledError, Future
from collections.abc import Generator
from typing import Any, override

from .request import Request


class FutureRequest(Request):
    """ A request wrapping an asyncio.Future. """

    def __init__(self, future: Future[None]):
        self._future = future

    @override
    async def wait(self) -> None:
        try:
            await self._future
        except (CancelledError, Exception): # noqa: S110 -- intentional: cancel is fire-and-forget
            pass

    @override
    def __await__(self) -> Generator[Any, None, None]:
        return self._future.__await__()

