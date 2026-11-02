import unittest

from soil.data import Path, Timestamp
from soil.nodes.receiver.typed.data import DataReceiverNode
from soil.nodes.receiver.typed.double import DoubleReceiverNode
from soil.nodes.receiver.typed.int import IntReceiverNode
from soil.nodes.receiver.typed.path import PathReceiverNode
from soil.nodes.receiver.typed.string import StringReceiverNode
from soil.requests.completed import CompletedRequest


def makeStub(nodeType):
    class StubNode(nodeType):
        """ Stub, das set abfängt und die Aufrufe mitzeichnet. """
        def __init__(self):
            self.setCalls = []

        def path(self):
            return Path()

        def provider(self):
            return None

        def receiver(self):
            return self         

        def acceptValue(self, value, path, timestamp):
            self.setCalls.append((value, timestamp))
            return CompletedRequest()

    return StubNode


class TestTypedReceiverNodes(unittest.IsolatedAsyncioTestCase):

    async def test_Integer(self):
        node = makeStub(IntReceiverNode)()
        await node.setInteger(42)
        value, timestamp = node.setCalls[0]
        self.assertEqual(value.intValue, 42)
        self.assertIsNone(timestamp)

    async def test_IntegerWithTimestamp(self):
        ts = Timestamp.current()
        node = makeStub(IntReceiverNode)()
        await node.setInteger(42, ts)
        value, timestamp = node.setCalls[0]
        self.assertEqual(value.intValue, 42)
        self.assertIs(timestamp, ts)

    async def test_Double(self):
        node = makeStub(DoubleReceiverNode)()
        await node.setDouble(3.14)
        value, timestamp = node.setCalls[0]
        self.assertEqual(value.doubleValue, 3.14)
        self.assertIsNone(timestamp)

    async def test_DoubleWithTimestamp(self):
        ts = Timestamp.current()
        node = makeStub(DoubleReceiverNode)()
        await node.setDouble(3.14, ts)
        value, timestamp = node.setCalls[0]
        self.assertEqual(value.doubleValue, 3.14)
        self.assertIs(timestamp, ts)

    async def test_String(self):
        node = makeStub(StringReceiverNode)()
        await node.setString("hello")
        value, timestamp = node.setCalls[0]
        self.assertEqual(value.stringValue, "hello")
        self.assertIsNone(timestamp)

    async def test_StringWithTimestamp(self):
        ts = Timestamp.current()
        node = makeStub(StringReceiverNode)()
        await node.setString("hello", ts)
        value, timestamp = node.setCalls[0]
        self.assertEqual(value.stringValue, "hello")
        self.assertIs(timestamp, ts)

    async def test_Data(self):
        node = makeStub(DataReceiverNode)()
        await node.setData(b"hello")
        value, timestamp = node.setCalls[0]
        self.assertEqual(value.dataValue, b"hello")
        self.assertIsNone(timestamp)

    async def test_DataWithTimestamp(self):
        ts = Timestamp.current()
        node = makeStub(DataReceiverNode)()
        await node.setData(b"hello", ts)
        value, timestamp = node.setCalls[0]
        self.assertEqual(value.dataValue, b"hello")
        self.assertIs(timestamp, ts)

    async def test_Path(self):
        expected = Path.of("a", "b")
        node = makeStub(PathReceiverNode)()
        node.setPath(expected)
        value, timestamp = node.setCalls[0]
        self.assertEqual(value.pathValue, expected)
        self.assertIsNone(timestamp)

    async def test_PathWithTimestamp(self):
        expected = Path.of("a", "b")
        ts = Timestamp.current()
        node = makeStub(PathReceiverNode)()
        node.setPath(expected, ts)
        value, timestamp = node.setCalls[0]
        self.assertEqual(value.pathValue, expected)
        self.assertIs(timestamp, ts)