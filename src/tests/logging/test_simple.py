import asyncio
import unittest

from soil.components import Receiver
from soil.data import Path
from soil.data.value import Value
from soil.logging.level import LogLevel
from soil.logging.simple import SimpleLogger
from soil.requests import CompletedRequest, Request


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


class TestSimpleLogger(unittest.IsolatedAsyncioTestCase):

    # MARK: Level

    async def test_DefaultLevelIsWarning(self):
        logger = SimpleLogger(Path.of("log"), StubReceiver())

        self.assertEqual(await logger.getLevel(), LogLevel.WARNING)

    async def test_ExplicitLevel(self):
        logger = SimpleLogger(Path.of("log"), StubReceiver(), level=LogLevel.ERROR)

        self.assertEqual(await logger.getLevel(), LogLevel.ERROR)

    async def test_SetLevel(self):
        logger = SimpleLogger(Path.of("log"), StubReceiver())

        await logger.setLevel(LogLevel.INFO)

        self.assertEqual(await logger.getLevel(), LogLevel.INFO)

    async def test_SetLevelNoneRestoresDefault(self):
        logger = SimpleLogger(Path.of("log"), StubReceiver())

        await logger.setLevel(LogLevel.DEBUG)
        await logger.setLevel(None)

        self.assertEqual(await logger.getLevel(), LogLevel.WARNING)

    # MARK: Log

    async def test_LogBelowLevelIsIgnored(self):
        receiver = StubReceiver()
        logger = SimpleLogger(Path.of("log"), receiver)

        request = logger.log(LogLevel.DEBUG, "too quiet")

        self.assertIsInstance(request, Request)
        await request
        self.assertEqual(receiver.values, [])

    async def test_LogAtLevelIsWritten(self):
        receiver = StubReceiver()
        logger = SimpleLogger(Path.of("log"), receiver)

        request = logger.log(LogLevel.WARNING, "hello")
        await request

        self.assertEqual(len(receiver.values), 1)
        value, path, timestamp = receiver.values[0]
        self.assertEqual(value, Value("hello"))
        self.assertEqual(path, Path.of("log") + [str(LogLevel.WARNING)])
        self.assertIsNotNone(timestamp)

    async def test_LogAboveLevelIsWritten(self):
        receiver = StubReceiver()
        logger = SimpleLogger(Path.of("log"), receiver)

        await logger.log(LogLevel.ERROR, "boom")

        self.assertEqual(len(receiver.values), 1)

    async def test_LogAfterSetLevelUsesNewLevel(self):
        receiver = StubReceiver()
        logger = SimpleLogger(Path.of("log"), receiver)

        await logger.setLevel(LogLevel.DEBUG)
        await logger.log(LogLevel.DEBUG, "now visible")

        self.assertEqual(len(receiver.values), 1)

    async def test_ConvenienceMethodsUseLevels(self):
        receiver = StubReceiver()
        logger = SimpleLogger(Path.of("log"), receiver)

        await logger.error("bad thing")
        await logger.debug("quiet")

        self.assertEqual(len(receiver.values), 1)
        value, _, _ = receiver.values[0]
        self.assertEqual(value, Value("bad thing"))

    # MARK: LogFormat

    async def test_LogFormatSubstitutesArguments(self):
        receiver = StubReceiver()
        logger = SimpleLogger(Path.of("log"), receiver)

        await logger.logFormat(LogLevel.ERROR, "%s has %d items", "node", 3)

        self.assertEqual(len(receiver.values), 1)
        value, _, _ = receiver.values[0]
        self.assertEqual(value, Value("node has 3 items"))

    async def test_LogFormatBelowLevelIsIgnored(self):
        receiver = StubReceiver()
        logger = SimpleLogger(Path.of("log"), receiver)

        await logger.logFormat(LogLevel.DEBUG, "%s", "ignored")

        self.assertEqual(receiver.values, [])

    # MARK: Children

    async def test_ChildLoggerInheritsLevelAndAppendsPath(self):
        receiver = StubReceiver()
        logger = SimpleLogger(Path.of("log"), receiver, level=LogLevel.DEBUG)

        child = logger.childLogger("sub")

        self.assertEqual(await child.getLevel(), LogLevel.DEBUG)
        await child.log(LogLevel.DEBUG, "from child")

        self.assertEqual(len(receiver.values), 1)
        value, path, _ = receiver.values[0]
        self.assertEqual(value, Value("from child"))
        self.assertEqual(path, Path.of("log") + ["sub", str(LogLevel.DEBUG)])

    async def test_ChildWithLevelOverridesLevel(self):
        receiver = StubReceiver()
        logger = SimpleLogger(Path.of("log"), receiver)

        child = logger.childWithLevel("sub", LogLevel.ERROR)

        await asyncio.sleep(0)

        self.assertEqual(await child.getLevel(), LogLevel.ERROR)
        self.assertEqual(await logger.getLevel(), LogLevel.WARNING)