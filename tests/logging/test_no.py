import unittest

from soil.logging.level import LogLevel
from soil.logging.no import NoLogger
from soil.requests import CompletedRequest


class TestNoLogger(unittest.IsolatedAsyncioTestCase):

    # MARK: Level

    async def test_DefaultLevelIsWarning(self):
        logger = NoLogger()

        self.assertEqual(await logger.getLevel(), LogLevel.WARNING)

    async def test_SetLevel(self):
        logger = NoLogger()

        request = logger.setLevel(LogLevel.INFO)

        self.assertIsInstance(request, CompletedRequest)
        self.assertEqual(await logger.getLevel(), LogLevel.INFO)

    async def test_SetLevelNoneRestoresDefault(self):
        logger = NoLogger()

        logger.setLevel(LogLevel.DEBUG)
        logger.setLevel(None)

        self.assertEqual(await logger.getLevel(), LogLevel.WARNING)

    async def test_TraceLevelIsPreserved(self):
        logger = NoLogger()

        logger.setLevel(LogLevel.TRACE)

        self.assertEqual(await logger.getLevel(), LogLevel.TRACE)

    # MARK: Log

    async def test_LogSwallowsEverything(self):
        logger = NoLogger()

        for level in (LogLevel.TRACE, LogLevel.DEBUG, LogLevel.INFO,
                      LogLevel.WARNING, LogLevel.ERROR):
            request = logger.log(level, "message", "with", "args")
            self.assertIsInstance(request, CompletedRequest)
            await request

    async def test_LogIgnoresAllLevels(self):
        logger = NoLogger()

        await logger.log(LogLevel.ERROR, "ignored")
        await logger.log(LogLevel.TRACE, "ignored")

        self.assertEqual(await logger.getLevel(), LogLevel.WARNING)

    # MARK: Children

    async def test_ChildLoggerIsNoLogger(self):
        logger = NoLogger()

        child = logger.childLogger("sub")

        self.assertIsInstance(child, NoLogger)

    async def test_ChildWithLevel(self):
        logger = NoLogger()

        child = logger.childWithLevel("sub", LogLevel.ERROR)

        self.assertIsInstance(child, NoLogger)
        self.assertEqual(await child.getLevel(), LogLevel.ERROR)

    async def test_ChildLoggerIsIndependent(self):
        logger = NoLogger()
        logger.setLevel(LogLevel.DEBUG)

        child = logger.childLogger("sub")

        self.assertEqual(await child.getLevel(), LogLevel.WARNING)