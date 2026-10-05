import unittest

from soil.data import Path
from soil.data.value import Value
from soil.nodes.provider.node import ProviderNode
from soil.nodes.provider.typed.data import DataProviderNode
from soil.nodes.provider.typed.double import DoubleProviderNode
from soil.nodes.provider.typed.int import IntProviderNode
from soil.nodes.provider.typed.path import PathProviderNode
from soil.nodes.provider.typed.string import StringProviderNode


def makeStub(nodeType):
    class StubNode(nodeType):
        """ Stub, das nur currentValue vorbestimmt. """
        def __init__(self, value):
            self._value = value

        @property
        def path(self) -> Path:
            return Path()

        @property
        def provider(self):
            return None

        async def currentValue(self):
            return self._value

    return StubNode


class TestTypedProviderNodes(unittest.IsolatedAsyncioTestCase):

    async def test_Integer(self):
        node = makeStub(IntProviderNode)(Value(42))
        self.assertEqual(await node.getInteger(), 42)

    async def test_IntegerReturnsNoneForNonInt(self):
        node = makeStub(IntProviderNode)(Value("nope"))
        self.assertIsNone(await node.getInteger())

    async def test_IntegerReturnsNoneWhenNoValue(self):
        node = makeStub(IntProviderNode)(None)
        self.assertIsNone(await node.getInteger())

    async def test_Double(self):
        node = makeStub(DoubleProviderNode)(Value(3.14))
        self.assertEqual(await node.getDouble(), 3.14)

    async def test_DoubleReturnsNoneForNonDouble(self):
        node = makeStub(DoubleProviderNode)(Value(1))
        self.assertIsNone(await node.getDouble())

    async def test_DoubleReturnsNoneWhenNoValue(self):
        node = makeStub(DoubleProviderNode)(None)
        self.assertIsNone(await node.getDouble())

    async def test_String(self):
        node = makeStub(StringProviderNode)(Value("hello"))
        self.assertEqual(await node.getString(), "hello")

    async def test_StringReturnsNoneForNonString(self):
        node = makeStub(StringProviderNode)(Value(5))
        self.assertIsNone(await node.getString())

    async def test_StringReturnsNoneWhenNoValue(self):
        node = makeStub(StringProviderNode)(None)
        self.assertIsNone(await node.getString())

    async def test_Data(self):
        node = makeStub(DataProviderNode)(Value(b"hello"))
        self.assertEqual(await node.getData(), b"hello")

    async def test_DataReturnsNoneForNonData(self):
        node = makeStub(DataProviderNode)(Value(123))
        self.assertIsNone(await node.getData())

    async def test_DataReturnsNoneWhenNoValue(self):
        node = makeStub(DataProviderNode)(None)
        self.assertIsNone(await node.getData())

    async def test_Path(self):
        expected = Path.of("a", "b")
        node = makeStub(PathProviderNode)(Value(expected))
        self.assertEqual(await node.gePath(), expected)

    async def test_PathReturnsNoneForNonPath(self):
        node = makeStub(PathProviderNode)(Value(123))
        self.assertIsNone(await node.gePath())

    async def test_PathReturnsNoneWhenNoValue(self):
        node = makeStub(PathProviderNode)(None)
        self.assertIsNone(await node.gePath())