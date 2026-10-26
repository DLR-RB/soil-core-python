import unittest

from soil.logging.level import LogLevel
from soil.logging.logger import Logger


class StubLogger(Logger):
    """ Logger, der nur das ABC erfuellt und Aufrufe mitzeichnet. """

    def __init__(self, level: LogLevel = LogLevel.WARNING):
        self.level = level
        self.logCalls = []
        self.childComponents = []

    def setLevel(self, level: LogLevel) -> object:
        self.level = level
        return None

    async def getLevel(self) -> LogLevel:
        return self.level

    def childLogger(self, component: str) -> 'StubLogger':
        self.childComponents.append(component)
        return StubLogger(level=self.level)

    def log(self, level: LogLevel, message: str, *args: object) -> object:
        self.logCalls.append((level, message, args))
        return None


class TestLogger(unittest.IsolatedAsyncioTestCase):

    async def test_ConvenienceMethodsDelegateToLog(self):
        cases = [
            (Logger.trace,   LogLevel.TRACE),
            (Logger.debug,   LogLevel.DEBUG),
            (Logger.info,    LogLevel.INFO),
            (Logger.warning, LogLevel.WARNING),
            (Logger.error,   LogLevel.ERROR),
        ]
        for method, expectedLevel in cases:
            with self.subTest(method = method.__name__):
                logger = StubLogger()

                method(logger, "msg %s", "arg")

                self.assertEqual(logger.logCalls, [(expectedLevel, "msg %s", ("arg",))])

    async def test_ConvenienceMethodPassesMessageThrough(self):
        logger = StubLogger()

        logger.error("plain message")

        self.assertEqual(logger.logCalls, [(LogLevel.ERROR, "plain message", ())])

    async def test_ChildWithLevelCreatesChild(self):
        logger = StubLogger()

        child = logger.childWithLevel("sub", LogLevel.ERROR)

        self.assertEqual(logger.childComponents, ["sub"])
        self.assertEqual(await child.getLevel(), LogLevel.ERROR)

    async def test_ChildWithLevelDoesNotChangeParent(self):
        logger = StubLogger(level=LogLevel.INFO)

        logger.childWithLevel("sub", LogLevel.DEBUG)

        self.assertEqual(await logger.getLevel(), LogLevel.INFO)

    async def test_ChildWithLevelForwardsArguments(self):
        logger = StubLogger()

        logger.childWithLevel("engine", LogLevel.TRACE)

        self.assertEqual(logger.childComponents, ["engine"])