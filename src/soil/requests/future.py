from typing import Any, Generator, override
from asyncio import Future, CancelledError

from .request import Request


class FutureRequest(Request):
    """ A request wrapping an asyncio.Future. """

    def __init__(self, future: Future[None]):
        self._future = future

    @override
    async def wait(self) -> None:
        try:
            await self._future
        except (CancelledError, Exception):
            pass

    @override
    def __await__(self) -> Generator[Any, None, None]:
        return self._future.__await__()

