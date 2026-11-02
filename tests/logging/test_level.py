import unittest

from soil.logging.level import LogLevel


class TestLogLevel(unittest.TestCase):

    def test_StringRoundTrip(self):
        for level in LogLevel:
            self.assertEqual(LogLevel.fromString(str(level)), level)

    def test_StringValues(self):
        self.assertEqual(str(LogLevel.TRACE), "trace")
        self.assertEqual(str(LogLevel.DEBUG), "debug")
        self.assertEqual(str(LogLevel.INFO), "info")
        self.assertEqual(str(LogLevel.WARNING), "warning")
        self.assertEqual(str(LogLevel.ERROR), "error")

    def test_FromString(self):
        self.assertEqual(LogLevel.fromString("trace"), LogLevel.TRACE)
        self.assertEqual(LogLevel.fromString("debug"), LogLevel.DEBUG)
        self.assertEqual(LogLevel.fromString("info"), LogLevel.INFO)
        self.assertEqual(LogLevel.fromString("warning"), LogLevel.WARNING)
        self.assertEqual(LogLevel.fromString("error"), LogLevel.ERROR)

    def test_FromStringInvalid(self):
        self.assertIsNone(LogLevel.fromString(""))
        self.assertIsNone(LogLevel.fromString("TRACE"))
        self.assertIsNone(LogLevel.fromString("Info"))
        self.assertIsNone(LogLevel.fromString("warn"))
        self.assertIsNone(LogLevel.fromString("unbekannt"))

    def test_StringValue(self):
        self.assertEqual(LogLevel.ERROR.stringValue, "error")

    def test_IntValues(self):
        self.assertEqual(LogLevel.TRACE, 0)
        self.assertEqual(LogLevel.ERROR, 4)
        self.assertTrue(LogLevel.DEBUG < LogLevel.WARNING)