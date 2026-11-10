import asyncio
import unittest

from soil.requests import Request
from soil.utils.actor import Actor, ActorClosedError, queued, queuedAsync, synchronized


class Worker(Actor):
    """ Test-Actor mit allen drei Annotationen. """

    def __init__(self):
        Actor.__init__(self)
        self.log = []
        self.gate = asyncio.Event()

    @synchronized
    async def step(self, name: str) -> None:
        self.log.append(("start", name))
        await asyncio.sleep(0.01)
        self.log.append(("end", name))

    @synchronized
    async def hold(self) -> None:
        """ Blockiert den Actor, bis das Gate geoeffnet wird. """
        await self.gate.wait()

    @synchronized
    async def boom(self) -> None:
        raise RuntimeError("boom")

    @queuedAsync
    def compute(self) -> int:
        return 42

    @queued
    async def work(self) -> int:
        return 7

    @queued(default=0)
    async def defaulted(self) -> int:
        return 7


class TestActor(unittest.IsolatedAsyncioTestCase):

    async def test_SynchronizedRunsSequentially(self):
        actor = Worker()

        first = actor.step("one")
        second = actor.step("two")

        await asyncio.wait_for(first, timeout=1)
        await asyncio.wait_for(second, timeout=1)
        await actor.shutdown()

        self.assertEqual(actor.log[0], ("start", "one"))
        self.assertEqual(actor.log[1], ("end", "one"))
        self.assertEqual(actor.log[2], ("start", "two"))
        self.assertEqual(actor.log[3], ("end", "two"))

    async def test_SynchronizedReturnsRequest(self):
        actor = Worker()

        request = actor.step("one")

        self.assertIsInstance(request, Request)
        await actor.shutdown()

    async def test_QueuedAsyncReturnsResult(self):
        actor = Worker()

        result = await actor.compute()

        self.assertEqual(result, 42)
        await actor.shutdown()

    async def test_QueuedReturnsFuture(self):
        actor = Worker()

        future = actor.work()

        self.assertIsInstance(future, asyncio.Future)
        self.assertEqual(await future, 7)
        await actor.shutdown()

    async def test_ShutdownIsIdempotent(self):
        actor = Worker()

        await actor.shutdown()
        await actor.shutdown()

    async def test_QueuedAsyncAfterShutdownRaises(self):
        actor = Worker()
        await actor.shutdown()

        with self.assertRaises(ActorClosedError):
            await actor.compute()

    async def test_QueuedAfterShutdownReturnsDefault(self):
        actor = Worker()
        await actor.shutdown()

        future = actor.defaulted()

        self.assertEqual(await future, 0)

    async def test_QueuedAfterShutdownWithoutDefaultRaises(self):
        actor = Worker()
        await actor.shutdown()

        future = actor.work()

        with self.assertRaises(ActorClosedError):
            await future