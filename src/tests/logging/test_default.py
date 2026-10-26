import unittest

from soil.components import Receiver
from soil.data import Path
from soil.data.value import Value
from soil.logging.default import DefaultLogger
from soil.logging.level import LogLevel
from soil.requests import CompletedRequest


class StubReceiver(Receiver):
    """ Receiver, der acceptValue-Aufrufe mitzeichnet. """

    def __init__(self):
        self.values = []

    def acceptValue(self, value, path, timestamp):
        self.values.append((value, path, timestamp))
        return CompletedRequest()

    def acceptSample(self, sample, path):
        return CompletedRequest()

    def acceptSamples(self, samples, path):
        return CompletedRequest()

    def accept(self, tree, path):
        return CompletedRequest()


class TestDefaultLogger(unittest.IsolatedAsyncioTestCase):

    # MARK: Level

    async def test_InitialLevel(self):
        logger = DefaultLogger(Path.of("log"), StubReceiver(), LogLevel.DEBUG)

        self.assertEqual(await logger.getLevel(), LogLevel.DEBUG)

    async def test_SetLevel(self):
        logger = DefaultLogger(Path.of("log"), StubReceiver(), LogLevel.WARNING)

        request = logger.setLevel(LogLevel.INFO)

        self.assertIsInstance(request, CompletedRequest)
        self.assertEqual(await logger.getLevel(), LogLevel.INFO)

    async def test_IsDisabled(self):
        logger = DefaultLogger(Path.of("log"), StubReceiver(), LogLevel.WARNING)

        self.assertFalse(logger.isDisabled(LogLevel.WARNING))
        self.assertFalse(logger.isDisabled(LogLevel.ERROR))
        self.assertTrue(logger.isDisabled(LogLevel.DEBUG))

    # MARK: Log

    async def test_LogBelowLevelIsIgnored(self):
        receiver = StubReceiver()
        logger = DefaultLogger(Path.of("log"), receiver, LogLevel.WARNING)

        request = logger.log(LogLevel.DEBUG, "too quiet")

        self.assertIsInstance(request, CompletedRequest)
        await request
        self.assertEqual(receiver.values, [])

    async def test_LogAtLevelIsWritten(self):
        receiver = StubReceiver()
        logger = DefaultLogger(Path.of("log"), receiver, LogLevel.WARNING)

        await logger.log(LogLevel.WARNING, "hello")

        self.assertEqual(len(receiver.values), 1)
        value, path, timestamp = receiver.values[0]
        self.assertEqual(value, Value("hello"))
        self.assertEqual(path, Path.of("log").appending(LogLevel.WARNING.stringValue))
        self.assertIsNotNone(timestamp)

    async def test_LogAboveLevelIsWritten(self):
        receiver = StubReceiver()
        logger = DefaultLogger(Path.of("log"), receiver, LogLevel.WARNING)

        await logger.log(LogLevel.ERROR, "boom")

        self.assertEqual(len(receiver.values), 1)

    async def test_LogFormatsArguments(self):
        receiver = StubReceiver()
        logger = DefaultLogger(Path.of("log"), receiver, LogLevel.INFO)

        await logger.log(LogLevel.INFO, "hello %s", "world")

        value, _, _ = receiver.values[0]
        self.assertEqual(value, Value("hello world"))

    async def test_LogAfterSetLevelUsesNewLevel(self):
        receiver = StubReceiver()
        logger = DefaultLogger(Path.of("log"), receiver, LogLevel.WARNING)

        await logger.setLevel(LogLevel.DEBUG)
        await logger.log(LogLevel.DEBUG, "now visible")

        self.assertEqual(len(receiver.values), 1)

    # MARK: Children

    async def test_ChildLoggerInheritsLevelAndAppendsPath(self):
        receiver = StubReceiver()
        logger = DefaultLogger(Path.of("log"), receiver, LogLevel.DEBUG)

        child = logger.childLogger("sub")

        self.assertEqual(await child.getLevel(), LogLevel.DEBUG)
        await child.log(LogLevel.DEBUG, "from child")

        value, path, _ = receiver.values[0]
        self.assertEqual(value, Value("from child"))
        self.assertEqual(path, Path.of("log").appending("sub").appending(LogLevel.DEBUG.stringValue))

    async def test_ChildLoggerWithExplicitLevel(self):
        receiver = StubReceiver()
        logger = DefaultLogger(Path.of("log"), receiver, LogLevel.WARNING)

        child = logger.childLogger("sub", LogLevel.ERROR)

        self.assertEqual(await child.getLevel(), LogLevel.ERROR)
        self.assertEqual(await logger.getLevel(), LogLevel.WARNING)

    async def test_ChildWithLevelFromBase(self):
        receiver = StubReceiver()
        logger = DefaultLogger(Path.of("log"), receiver, LogLevel.WARNING)

        child = logger.childWithLevel("sub", LogLevel.ERROR)

        self.assertEqual(await child.getLevel(), LogLevel.ERROR)