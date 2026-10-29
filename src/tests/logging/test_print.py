import io
import unittest
from contextlib import redirect_stdout
from io import StringIO

from soil.data import Path
from soil.logging import LogLevel, PrintLogger, Logger


def captureLog(logger: Logger, level: LogLevel, message: str, *args: object) -> str:
    """ Logger-Aufruf ausfuehren und die Konsolenausgabe zurueckgeben. """
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        logger.log(level, message, *args)
    return buffer.getvalue()


class TestPrintLogger(unittest.IsolatedAsyncioTestCase):

    # MARK: Level

    async def test_DefaultLevelIsWarning(self):
        logger = PrintLogger()

        self.assertEqual(await logger.getLevel(), LogLevel.WARNING)

    async def test_ExplicitLevel(self):
        logger = PrintLogger(level=LogLevel.ERROR)

        self.assertEqual(await logger.getLevel(), LogLevel.ERROR)

    async def test_SetLevel(self):
        logger = PrintLogger()

        request = logger.setLevel(LogLevel.INFO)

        self.assertIsInstance(request, object)
        self.assertEqual(await logger.getLevel(), LogLevel.INFO)

    async def test_SetLevelNoneRestoresDefault(self):
        logger = PrintLogger()

        logger.setLevel(LogLevel.DEBUG)
        logger.setLevel(None)

        self.assertEqual(await logger.getLevel(), LogLevel.WARNING)

    async def test_TraceLevelIsPreserved(self):
        logger = PrintLogger(level=LogLevel.TRACE)

        self.assertEqual(await logger.getLevel(), LogLevel.TRACE)

    # MARK: Log

    async def test_LogBelowLevelPrintsNothing(self):
        logger = PrintLogger()

        output = captureLog(logger, LogLevel.DEBUG, "quiet")

        self.assertEqual(output, "")

    async def test_LogAtLevelPrints(self):
        logger = PrintLogger(path=Path.of("a"))

        output = captureLog(logger, LogLevel.WARNING, "hello")

        self.assertIn("hello", output)
        self.assertIn("a", output)
        self.assertIn(str(LogLevel.WARNING).upper(), output)

    async def test_LogFormatsArguments(self):
        logger = PrintLogger(level=LogLevel.INFO)

        output = captureLog(logger, LogLevel.INFO, "hello {}", "world")

        self.assertIn("hello world", output)


    async def test_LogReturnsCompletedRequest(self):
        logger = PrintLogger()

        log = StringIO()
        with redirect_stdout(log):
            request = logger.log(LogLevel.WARNING, "msg")

        await request

    # MARK: Children

    async def test_ChildLoggerAppendsPathComponent(self):
        logger = PrintLogger(path=Path.of("a", "b"))

        child = logger.childLogger("sub")

        self.assertIsInstance(child, PrintLogger)
        output = captureLog(child, LogLevel.ERROR, "from child")
        self.assertIn("from child", output)
        self.assertIn("sub", output)

    async def test_ChildWithLevelSetsLevel(self):
        logger = PrintLogger()

        child = logger.childWithLevel("sub", LogLevel.ERROR)

        self.assertEqual(await child.getLevel(), LogLevel.ERROR)
        self.assertEqual(await logger.getLevel(), LogLevel.WARNING)