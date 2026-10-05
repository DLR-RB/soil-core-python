import unittest

from soil.data import Path, Sample, SampleTree, Timestamp
from soil.data.value import Value
from soil.nodes.provider.node import ProviderNode
from soil.nodes.provider.defaults.node import DefaultProviderNode
from soil.nodes.provider.defaults.int import DefaultIntProviderNode
from soil.nodes.provider.defaults.data import DefaultDataProviderNode
from soil.nodes.provider.defaults.double import DefaultDoubleProviderNode
from soil.nodes.provider.defaults.path import DefaultPathProviderNode
from soil.nodes.provider.defaults.string import DefaultStringProviderNode


class StubProvider:
    """ Duck-getypter Provider, der Aufrufe mitzeichnet. """

    def __init__(self, sample=None):
        self.returnValue = sample
        self.currentSampleCalls = []
        self.sampleCalls = []
        self.treeCalls = []
        self.treeResult = SampleTree([])

    async def currentSample(self, path):
        self.currentSampleCalls.append(path)
        return self.returnValue

    async def sample(self, path, beforeOrAt):
        self.sampleCalls.append((path, beforeOrAt))
        return self.returnValue

    async def tree(self, path, start, end, depth, level):
        self.treeCalls.append((path, start, end, depth, level))
        return self.treeResult


class StubNode(ProviderNode):
    """ Stub, der provider und path vorbestimmt. """

    def __init__(self, provider, path):
        self._provider = provider
        self._path = path

    def provider(self):
        return self._provider

    def path(self):
        return self._path


class TestProviderNode(unittest.IsolatedAsyncioTestCase):

    async def test_CurrentValueReturnsValue(self):
        provider = StubProvider(Sample(Value(42)))
        node = StubNode(provider, Path.of("a"))

        self.assertEqual((await node.currentValue()).intValue, 42)

    async def test_CurrentValueReturnsNoneWhenNoSample(self):
        provider = StubProvider(None)
        node = StubNode(provider, Path.of("a"))

        self.assertIsNone(await node.currentValue())

    async def test_IsNull(self):
        provider = StubProvider(Sample(Value(1)))
        node = StubNode(provider, Path.of("a"))

        self.assertFalse(await node.isNull())

    async def test_IsNullReturnsNoneWhenNoSample(self):
        provider = StubProvider(None)
        node = StubNode(provider, Path.of("a"))

        self.assertIsNone(await node.isNull())

    async def test_CurrentSampleDelegatesToProvider(self):
        path = Path.of("a", "b")
        provider = StubProvider(Sample(Value(1)))
        node = StubNode(provider, path)

        await node.currentSample()

        self.assertEqual(provider.currentSampleCalls, [path])

    async def test_SampleDelegatesToProvider(self):
        path = Path.of("a")
        ts = Timestamp.current()
        provider = StubProvider(Sample(Value(1)))
        node = StubNode(provider, path)

        await node.sample(ts)

        self.assertEqual(provider.sampleCalls, [(path, ts)])

    async def test_CurrentTreeDelegatesToProvider(self):
        path = Path.of("a")
        provider = StubProvider()
        node = StubNode(provider, path)

        tree = await node.currentTree(depth=2)

        calledPath, _, _, depth, _ = provider.treeCalls[0]
        self.assertEqual(calledPath, path)
        self.assertEqual(depth, 2)
        self.assertIs(tree, provider.treeResult)

    async def test_ChildCreatesDefaultNode(self):
        provider = StubProvider()
        node = StubNode(provider, Path.of("a"))

        child = node.child("b")

        self.assertIsInstance(child, DefaultProviderNode)
        self.assertIs(child.provider(), provider)
        self.assertEqual(child.path(), Path.of("a", "b"))

    async def test_IntChildCreatesTypedNode(self):
        provider = StubProvider()
        node = StubNode(provider, Path.of("a"))

        child = node.intChild("b")

        self.assertIsInstance(child, DefaultIntProviderNode)
        self.assertIs(child.provider(), provider)
        self.assertEqual(child.path(), Path.of("a", "b"))


    async def test_DoubleChildCreatesTypedNode(self):
        provider = StubProvider()
        node = StubNode(provider, Path.of("a"))

        child = node.doubleChild("b")

        self.assertIsInstance(child, DefaultDoubleProviderNode)
        self.assertIs(child.provider(), provider)
        self.assertEqual(child.path(), Path.of("a", "b"))

    async def test_StringChildCreatesTypedNode(self):
        provider = StubProvider()
        node = StubNode(provider, Path.of("a"))

        child = node.stringChild("b")

        self.assertIsInstance(child, DefaultStringProviderNode)
        self.assertIs(child.provider(), provider)
        self.assertEqual(child.path(), Path.of("a", "b"))

    async def test_DataChildCreatesTypedNode(self):
        provider = StubProvider()
        node = StubNode(provider, Path.of("a"))

        child = node.dataChild("b")

        self.assertIsInstance(child, DefaultDataProviderNode)
        self.assertIs(child.provider(), provider)
        self.assertEqual(child.path(), Path.of("a", "b"))

    async def test_PathChildCreatesTypedNode(self):
        provider = StubProvider()
        node = StubNode(provider, Path.of("a"))

        child = node.pathChild("b")

        self.assertIsInstance(child, DefaultPathProviderNode)
        self.assertIs(child.provider(), provider)
        self.assertEqual(child.path(), Path.of("a", "b"))