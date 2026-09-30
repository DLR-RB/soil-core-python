import asyncio
from collections.abc import Awaitable, Generator
from typing import Any, override

from .request import Request


async def _run(awaitable: Awaitable[None]) -> None:
    await awaitable


class AsyncRequest(Request):
    """An asynchronous request.

    Wraps an async operation in an asyncio.Task and provides a method
    to wait for its completion.
    """

    def __init__(self, operation: Awaitable[None]) -> None:
        self._task: asyncio.Task[None] = asyncio.create_task(_run(operation))

    @override
    async def wait(self) -> None:
        """Wait for the request to complete."""
        await self._task

    @override
    def __await__(self) -> Generator[Any, Any, None]:
        return self._task.__await__()