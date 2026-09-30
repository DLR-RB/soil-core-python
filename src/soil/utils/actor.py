from asyncio import (
    CancelledError,
    Future,
    InvalidStateError,
    Queue,
    QueueEmpty,
    create_task,
    get_running_loop,
)
from collections.abc import Awaitable, Callable
from contextlib import suppress
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Concatenate,
    ParamSpec,
    TypeVar,
    overload,
)

if TYPE_CHECKING:
    from types import CoroutineType

from ..requests import FutureRequest, Request

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

    Actor methods must not await other synchronized methods on the same actor.
    """

    def __init__(self):
        self._queue: Queue[tuple[Callable[[], Awaitable[Any]], Future[Any]] | _StopSentinel] = Queue()
        self._task = create_task(self._run())
        self._isClosed: bool = False
        """ Indicate if the actor queue is closed """

    async def _run(self):
        while True:
            try:
                item = await self._queue.get()
            except CancelledError:
                return
            except Exception as e:
                print(f"Actor: Failed to get next task ({type(e)}): {e}")
                return
            if isinstance(item, _StopSentinel):
                # Queue finished due to actor shutdown
                self._failAllPendingWork()
                return
            work, future = item
            try:
                result = await work()
                # TODO: Fix type annotations properly
                try:
                    result = await result
                except:
                    pass
            except CancelledError:
                future.cancel()
                self._failAllPendingWork()
                return
            except Exception as e:
                # Try to set the exception for the future,
                # catch error if the future is already completed
                with suppress(InvalidStateError):
                    future.set_exception(e)
                continue
            # Try to set the result for the future,
            # catch error if the future is already completed
            with suppress(InvalidStateError):
                future.set_result(result)

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

    async def shutdown(self):
        """
        Finish the actor queue, then close the run task and prevent any future calls
        """
        if self._isClosed:
            return
        await self._queue.put(_StopSentinel())
        self._isClosed = True

    def _submit(self, work: Callable[[], Awaitable[None]]) -> Request:
        """ Create a future with the work item to be done, and put it one the queue. """
        future = self._enqueue(work, default = None)
        return FutureRequest(future)

    def _enqueue(
        self,
        work: Callable[[], Awaitable[R]],
        *,
        default: R | _Missing = _MISSING,
    ) -> Future[R]:
        """ Create a future with the work item to be done, and put it one the queue. """
        future: Future[R] = get_running_loop().create_future()
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
    Run an async function on the actor, and return a request
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

def queuedAsync(
    method: Callable[Concatenate[SelfT, P], R],
) -> Callable[Concatenate[SelfT, P], 'CoroutineType[Any, Any, R]']:
    """
    Run a synchronous function on the actor queue, returning the result
    """
    @wraps(method)
    async def wrapper(
        self: SelfT,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        async def work() -> R:
            return method(self, *args, **kwargs)
        future = self._enqueue(work) # pyright: ignore[reportPrivateUsage]
        return await future
    return wrapper

@overload
def queued(
    fn: Callable[Concatenate[SelfT, P], Awaitable[R]],
    /,
) -> Callable[Concatenate[SelfT, P], Future[R]]:
    """
    Run an async function on the actor, and return a future
    """

@overload
def queued(
    *,
    default: R,
) -> Callable[
    [Callable[Concatenate[SelfT, P], Awaitable[R]]],
    Callable[Concatenate[SelfT, P], Future[R]],
]:
    """
    Run an async function on the actor, and return a future
    """


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
