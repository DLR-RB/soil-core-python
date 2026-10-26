import unittest
from contextlib import redirect_stdout
from io import StringIO

from soil.data import Path, Sample, SampleTree, Timestamp
from soil.data.value import Value
from soil.debug.print import PrintReceiver


class TestPrintReceiver(unittest.TestCase):

    def test_AcceptPrintsSample(self):
        receiver = PrintReceiver()
        tree = SampleTree([Sample(Value(42))])

        log = StringIO()
        with redirect_stdout(log):
            receiver.accept(tree, Path.of("a"))

        output = log.getvalue()
        self.assertIn("a: 42", output)

    def test_AcceptPrintsPathHierarchy(self):
        receiver = PrintReceiver()
        tree = SampleTree(
            children={"child": SampleTree([Sample(Value(1))])}
        )

        log = StringIO()
        with redirect_stdout(log):
            receiver.accept(tree, Path.of("a"))

        self.assertIn("a>child: 1", log.getvalue())

    def test_AcceptPrintsTimestamp(self):
        now = Timestamp.current()
        receiver = PrintReceiver()
        tree = SampleTree([Sample(Value(1), now)])

        log = StringIO()
        with redirect_stdout(log):
            receiver.accept(tree, Path.of("a"))

        expected = now.astimezone().strftime("%H:%M:%S %d.%m.%Y")
        self.assertIn(f"a: 1 ({expected})", log.getvalue())

    def test_ConvertPath(self):
        receiver = PrintReceiver()
        self.assertEqual(receiver.convertPath(Path.of("a", "b", "c")), "a>b>c")

    def test_ConvertTimeNone(self):
        receiver = PrintReceiver()
        self.assertEqual(receiver.convertTime(None), "Now")

    def test_ConvertTimeCustomFormat(self):
        now = Timestamp.current()
        receiver = PrintReceiver(dateFormat="%Y")

        year = receiver.convertTime(now)
        self.assertTrue(year.isdigit())
        self.assertEqual(year, now.astimezone().strftime("%Y"))