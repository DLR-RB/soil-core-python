from asyncio import Queue, Future, create_task, get_event_loop, CancelledError, QueueEmpty
from typing import Any, Awaitable, Callable, overload
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Concatenate, ParamSpec, TypeVar

from ..requests import Request, FutureRequest, CompletedRequest

P = ParamSpec("P")
R = TypeVar("R")

from enum import Enum

class _Missing(Enum):
    TOKEN = 0

_MISSING = _Missing.TOKEN

class _StopSentinel:
    pass

class ActorClosedError(Exception):
    pass


class Actor:
    """
    Base class for actor-like objects with serial task execution.

    The actor uses an asyncio Queue to schedule method calls sequentially,
    and runs an asyncio Task to process the queue.

    The annotation `@synchronized` can be used on methods to run them on the Queue,
    returning a `Request`. Use `@queued` to only return an asyncio Future.
    """

    def __init__(self):
        self._queue: Queue[tuple[Callable[[], Awaitable[Any]], Future[Any]] | _StopSentinel] = Queue()
        self._task = create_task(self._run())
        self._isClosed: bool = False

    async def _run(self):
        try:
            while True:
                item = await self._queue.get()
                if isinstance(item, _StopSentinel):
                    # Queue finished due to actor shutdown
                    break
                work, future = item
                try:
                    result = await work()
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
        except CancelledError:
            raise

        except Exception:
            # Fatal actor failure.
            raise

        finally:
            self._failAllPendingWork()

    def _failAllPendingWork(self) -> None:
        while True:
            try:
                item = self._queue.get_nowait()
            except QueueEmpty:
                break
            if isinstance(item, _StopSentinel):
                continue
            _, future = item
            if future.done():
                continue
            future.set_exception(ActorClosedError())

    async def shutdownActorQueue(self):
        if self._isClosed:
            return
        self._isClosed = True
        await self._queue.put(_StopSentinel())

    def _submit(self, work: Callable[[], Awaitable[None]]) -> Request:
        """ Create a future with the work item to be done, and put it one the queue. """
        if self._isClosed:
            return CompletedRequest()
        future = self._enqueue(work, default = None)
        return FutureRequest(future)

    def _enqueue(
        self,
        work: Callable[[], Awaitable[R]],
        *,
        default: R | _Missing = _MISSING,
    ) -> Future[R]:
        """ Create a future with the work item to be done, and put it one the queue. """
        loop = get_event_loop()
        future: Future[R] = loop.create_future()
        if not self._isClosed:
            self._queue.put_nowait((work, future))
            return future
        if default is _MISSING:
            future.set_exception(ActorClosedError())
            return future
        future.set_result(default)
        return future


SelfT = TypeVar("SelfT", bound=Actor)


def synchronized(
    method: Callable[Concatenate[SelfT, P], Awaitable[None]],
) -> Callable[Concatenate[SelfT, P], Request]:
    """
    An annotation to synchronize method access on an `Actor`.
    """
    @wraps(method)
    def wrapper(
        self: SelfT,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Request:
        async def work() -> None:
            return await method(self, *args, **kwargs)
        return self._submit(work) # pyright: ignore[reportPrivateUsage]
    return wrapper

@overload
def queued(
    fn: Callable[Concatenate[SelfT, P], Awaitable[R]],
    /,
) -> Callable[Concatenate[SelfT, P], Future[R]]: ...


@overload
def queued(
    *,
    default: R,
) -> Callable[
    [Callable[Concatenate[SelfT, P], Awaitable[R]]],
    Callable[Concatenate[SelfT, P], Future[R]],
]: ...


def queued(
    fn: Callable[Concatenate[SelfT, P], Awaitable[R]] | None = None,
    /,
    *,
    default: R | _Missing = _MISSING,
) -> (
    Callable[Concatenate[SelfT, P], Future[R]]
    | Callable[
        [Callable[Concatenate[SelfT, P], Awaitable[R]]],
        Callable[Concatenate[SelfT, P], Future[R]],
    ]
):
    def decorator(
        fn: Callable[Concatenate[SelfT, P], Awaitable[R]],
    ) -> Callable[Concatenate[SelfT, P], Future[R]]:
        @wraps(fn)
        def wrapper(
            self: SelfT,
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> Future[R]:
            async def work() -> R:
                return await fn(self, *args, **kwargs)

            return self._enqueue(work, default=default)  # pyright: ignore[reportPrivateUsage]

        return wrapper

    if fn is None:
        return decorator

    return decorator(fn)