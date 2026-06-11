import asyncio
from typing import Any, Awaitable, Callable

from ..requests.request import Request, AsyncRequest, CompletedRequest


class Actor:
    """Base class for actor-like objects with serial task execution."""

    def __init__(self):
        self._queue: asyncio.Queue[tuple[Callable[[], Awaitable[Any]], asyncio.Future[Any]]] = asyncio.Queue()
        self._task = asyncio.create_task(self._run())

    async def _run(self):
        while True:
            func, fut = await self._queue.get()
            try:
                result = await func()
                fut.set_result(result)
            except Exception as e:
                fut.set_exception(e)

    def _submit(self, func: Callable[[], Awaitable[None]]) -> Request:
        loop = asyncio.get_event_loop()
        fut: asyncio.Future[None] = loop.create_future()
        self._queue.put_nowait((func, fut))
        return AsyncRequest(fut)

    def noOp(self) -> Request:
        """Returns a request that is immediately done."""
        return CompletedRequest()