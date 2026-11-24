import unittest

from soil.logging.level import LogLevel
from soil.logging.logger import Logger
from soil.logging.optional import OptionalLogger
from soil.requests import CompletedRequest


class StubLogger(Logger):
    """ Logger, der Aufrufe mitzeichnet. """

    def __init__(self, level: LogLevel = LogLevel.WARNING):
        self.level = level
        self.messages = []
        self.childComponents = []

    def setLevel(self, level: LogLevel) -> object:
        self.level = level
        return CompletedRequest()

    async def getLevel(self) -> LogLevel:
        return self.level

    def childLogger(self, component: str) -> 'StubLogger':
        self.childComponents.append(component)
        return StubLogger(level=self.level)

    def log(self, level: LogLevel, message: str, *args: object) -> object:
        self.messages.append((level, message))
        return CompletedRequest()


class TestOptionalLogger(unittest.IsolatedAsyncioTestCase):

    async def test_WrapsNoneByDefault(self):
        wrapper = OptionalLogger()

        self.assertIsNone(wrapper.getLogger())

    async def test_LogWithoutLoggerIsNoOp(self):
        wrapper = OptionalLogger()

        request = wrapper.log(LogLevel.ERROR, "nobody hears me")

        await request
        self.assertIsNone(wrapper.getLogger())

    async def test_GetLevelWithoutLoggerIsWarning(self):
        wrapper = OptionalLogger()

        self.assertEqual(await wrapper.getLevel(), LogLevel.WARNING)

    async def test_SetLevelWithoutLoggerIsNoOp(self):
        wrapper = OptionalLogger()

        request = wrapper.setLevel(LogLevel.ERROR)

        await request
        self.assertEqual(await wrapper.getLevel(), LogLevel.WARNING)

    async def test_ChildLoggerWithoutLoggerIsEmptyWrapper(self):
        wrapper = OptionalLogger()

        child = wrapper.childLogger("sub")

        self.assertIsInstance(child, OptionalLogger)
        self.assertIsNone(child.getLogger())



    async def test_SetAndGetLogger(self):
        wrapper = OptionalLogger()
        logger = StubLogger()

        wrapper.setLogger(logger)

        self.assertIs(wrapper.getLogger(), logger)

    async def test_GetLevelDelegates(self):
        logger = StubLogger(level=LogLevel.ERROR)
        wrapper = OptionalLogger(logger)

        self.assertEqual(await wrapper.getLevel(), LogLevel.ERROR)

    async def test_SetLevelDelegates(self):
        logger = StubLogger()
        wrapper = OptionalLogger(logger)

        await wrapper.setLevel(LogLevel.DEBUG)

        self.assertEqual(logger.level, LogLevel.DEBUG)

    async def test_LogDelegates(self):
        logger = StubLogger()
        wrapper = OptionalLogger(logger)

        await wrapper.log(LogLevel.INFO, "hello there")

        self.assertEqual(logger.messages, [(LogLevel.INFO, "hello there")])

    async def test_ChildLoggerDelegates(self):
        logger = StubLogger()
        wrapper = OptionalLogger(logger)

        child = wrapper.childLogger("sub")

        self.assertEqual(logger.childComponents, ["sub"])
        self.assertIsInstance(child, StubLogger)

    async def test_ChildLoggerWithLevelDelegates(self):
        logger = StubLogger()
        wrapper = OptionalLogger(logger)

        child = wrapper.childLogger("sub", LogLevel.ERROR)

        self.assertEqual(logger.childComponents, ["sub"])
        self.assertEqual(await child.getLevel(), LogLevel.ERROR)



    async def test_LoggerCanBeSetLater(self):
        wrapper = OptionalLogger()
        wrapper.log(LogLevel.ERROR, "lost")

        logger = StubLogger()
        wrapper.setLogger(logger)

        await wrapper.log(LogLevel.ERROR, "arrived")

        self.assertEqual(logger.messages, [(LogLevel.ERROR, "arrived")])