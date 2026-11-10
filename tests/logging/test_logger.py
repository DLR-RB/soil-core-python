import unittest
from typing import Any, override

from soil.logging.level import LogLevel
from soil.logging.logger import Logger
from soil.requests import CompletedRequest, Request


class StubLogger(Logger):
    """ Logger, der nur das ABC erfuellt und Aufrufe mitzeichnet. """

    def __init__(self, level: LogLevel = LogLevel.WARNING):
        self.level = level
        self.logCalls: list[tuple[LogLevel, str, Any]] = []
        self.childComponents: list[str] = []

    @override
    def setLevel(self, level: LogLevel) -> Request:
        self.level = level
        return CompletedRequest()

    @override
    async def getLevel(self) -> LogLevel:
        return self.level

    @override
    def childLogger(self, component: str) -> 'StubLogger':
        self.childComponents.append(component)
        return StubLogger(level=self.level)

    @override
    def log(self, level: LogLevel, message: str, *args: object) -> Request:
        self.logCalls.append((level, message, args))
        return CompletedRequest()


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