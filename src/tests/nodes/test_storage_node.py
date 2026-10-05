import unittest

from soil.data import Path, Sample, SampleTree, Timestamp
from soil.data.value import Value
from soil.nodes.storage.node import StorageNode
from soil.nodes.storage.defaults.node import DefaultStorageNode
from soil.nodes.storage.defaults.int import DefaultIntStorageNode
from soil.nodes.storage.defaults.double import DefaultDoubleStorageNode
from soil.nodes.storage.defaults.string import DefaultStringStorageNode
from soil.nodes.storage.defaults.data import DefaultDataStorageNode
from soil.nodes.storage.defaults.path import DefaultPathStorageNode


class StubStorage:
    """ Duck-getypter Storage, der Aufrufe mitzeichnet. """

    def __init__(self):
        self.currentSampleCalls = []
        self.sampleCalls = []
        self.treeCalls = []
        self.valueCalls = []
        self.acceptSampleCalls = []
        self.acceptSamplesCalls = []
        self.acceptTreeCalls = []
        self.deleteCalls = []

    # MARK: Provider

    async def currentSample(self, path):
        self.currentSampleCalls.append(path)
        return None

    async def sample(self, path, beforeOrAt):
        self.sampleCalls.append((path, beforeOrAt))
        return None

    async def tree(self, path, start, end, depth, level):
        self.treeCalls.append((path, start, end, depth, level))
        return SampleTree([])

    # MARK: Receiver

    def acceptValue(self, value, path, timestamp):
        self.valueCalls.append((value, path, timestamp))

    def acceptSample(self, sample, path):
        self.acceptSampleCalls.append((sample, path))

    def acceptSamples(self, samples, path):
        self.acceptSamplesCalls.append((samples, path))

    def accept(self, tree, path):
        self.acceptTreeCalls.append((tree, path))

    # MARK: Storage

    async def delete(self, path, start, end, depth):
        self.deleteCalls.append((path, start, end, depth))


class StubNode(StorageNode):
    """ Stub, der storage und path vorbestimmt. """

    def __init__(self, storage, path):
        self._storage = storage
        self._path = path

    def storage(self):
        return self._storage

    def path(self):
        return self._path


class TestStorageNode(unittest.IsolatedAsyncioTestCase):

    def test_ProviderReturnsStorage(self):
        storage = StubStorage()
        node = StubNode(storage, Path.of("a"))

        self.assertIs(node.provider(), storage)

    def test_ReceiverReturnsStorage(self):
        storage = StubStorage()
        node = StubNode(storage, Path.of("a"))

        self.assertIs(node.receiver(), storage)

    async def test_DeleteDelegatesToStorage(self):
        path = Path.of("a")
        storage = StubStorage()
        node = StubNode(storage, path)

        ts = Timestamp.current()
        await node.delete(ts, None, 2)

        self.assertEqual(storage.deleteCalls, [(path, ts, None, 2)])

    async def test_DeleteHistoryDeletesOnlyThisNode(self):
        path = Path.of("a")
        storage = StubStorage()
        node = StubNode(storage, path)

        await node.deleteHistory()

        self.assertEqual(storage.deleteCalls, [(path, None, None, 0)])

    async def test_DeleteTreeDeletesFullSubtree(self):
        path = Path.of("a")
        storage = StubStorage()
        node = StubNode(storage, path)

        await node.deleteTree()

        self.assertEqual(storage.deleteCalls, [(path, None, None, None)])

    def test_ChildCreatesDefaultNode(self):
        storage = StubStorage()
        node = StubNode(storage, Path.of("a"))

        child = node.child("b")

        self.assertIsInstance(child, DefaultStorageNode)
        self.assertIs(child.storage(), storage)
        self.assertEqual(child.path(), Path.of("a", "b"))

    def test_IntChildCreatesTypedNode(self):
        storage = StubStorage()
        node = StubNode(storage, Path.of("a"))

        child = node.intChild("b")

        self.assertIsInstance(child, DefaultIntStorageNode)
        self.assertIs(child.storage(), storage)
        self.assertEqual(child.path(), Path.of("a", "b"))

    def test_DoubleChildCreatesTypedNode(self):
        storage = StubStorage()
        node = StubNode(storage, Path.of("a"))

        child = node.doubleChild("b")

        self.assertIsInstance(child, DefaultDoubleStorageNode)
        self.assertIs(child.storage(), storage)
        self.assertEqual(child.path(), Path.of("a", "b"))

    def test_StringChildCreatesTypedNode(self):
        storage = StubStorage()
        node = StubNode(storage, Path.of("a"))

        child = node.stringChild("b")

        self.assertIsInstance(child, DefaultStringStorageNode)
        self.assertIs(child.storage(), storage)
        self.assertEqual(child.path(), Path.of("a", "b"))

    def test_DataChildCreatesTypedNode(self):
        storage = StubStorage()
        node = StubNode(storage, Path.of("a"))

        child = node.dataChild("b")

        self.assertIsInstance(child, DefaultDataStorageNode)
        self.assertIs(child.storage(), storage)
        self.assertEqual(child.path(), Path.of("a", "b"))

    def test_PathChildCreatesTypedNode(self):
        storage = StubStorage()
        node = StubNode(storage, Path.of("a"))

        child = node.pathChild("b")

        self.assertIsInstance(child, DefaultPathStorageNode)
        self.assertIs(child.storage(), storage)
        self.assertEqual(child.path(), Path.of("a", "b"))