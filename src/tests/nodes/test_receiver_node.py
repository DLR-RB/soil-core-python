import unittest

from soil.data import Path, Sample, SampleTree, Timestamp
from soil.data.value import Value
from soil.nodes.receiver.defaults.data import DefaultDataReceiverNode
from soil.nodes.receiver.defaults.double import DefaultDoubleReceiverNode
from soil.nodes.receiver.defaults.int import DefaultIntReceiverNode
from soil.nodes.receiver.defaults.node import DefaultReceiverNode
from soil.nodes.receiver.defaults.path import DefaultPathReceiverNode
from soil.nodes.receiver.defaults.string import DefaultStringReceiverNode
from soil.nodes.receiver.node import ReceiverNode


class StubReceiver:
    """ Duck-getypter Receiver, der Aufrufe mitzeichnet. """

    def __init__(self):
        self.valueCalls = []
        self.sampleCalls = []
        self.samplesCalls = []
        self.treeCalls = []

    def acceptValue(self, value, path, timestamp):
        self.valueCalls.append((value, path, timestamp))

    def acceptSample(self, sample, path):
        self.sampleCalls.append((sample, path))

    def acceptSamples(self, samples, path):
        self.samplesCalls.append((samples, path))

    def accept(self, tree, path):
        self.treeCalls.append((tree, path))


class StubNode(ReceiverNode):
    """ Stub, der receiver und path vorbestimmt. """

    def __init__(self, receiver, path):
        self._receiver = receiver
        self._path = path

    def receiver(self):
        return self._receiver

    def path(self):
        return self._path


class TestReceiverNode(unittest.TestCase):

    def test_SetDelegatesToReceiver(self):
        path = Path.of("a")
        receiver = StubReceiver()
        node = StubNode(receiver, path)

        node.set(Value(42))

        value, calledPath, timestamp = receiver.valueCalls[0]
        self.assertEqual(value.intValue, 42)
        self.assertEqual(calledPath, path)
        self.assertIsNone(timestamp)

    def test_SetPassesTimestamp(self):
        ts = Timestamp.current()
        receiver = StubReceiver()
        node = StubNode(receiver, Path.of("a"))

        node.set(Value(1), ts)

        _, _, timestamp = receiver.valueCalls[0]
        self.assertIs(timestamp, ts)

    def test_SetNullUsesNullValue(self):
        receiver = StubReceiver()
        node = StubNode(receiver, Path.of("a"))

        node.setNull()

        value, _, _ = receiver.valueCalls[0]
        self.assertTrue(value.isNull)

    def test_SetSampleDelegatesToReceiver(self):
        path = Path.of("a")
        sample = Sample(Value(1))
        receiver = StubReceiver()
        node = StubNode(receiver, path)

        node.setSample(sample)

        self.assertEqual(receiver.sampleCalls, [(sample, path)])

    def test_SetSamplesDelegatesToReceiver(self):
        path = Path.of("a")
        samples = [Sample(Value(1)), Sample(Value(2))]
        receiver = StubReceiver()
        node = StubNode(receiver, path)

        node.setSamples(samples)

        self.assertEqual(receiver.samplesCalls, [(samples, path)])

    def test_SetTreeDelegatesToReceiver(self):
        path = Path.of("a")
        tree = SampleTree([])
        receiver = StubReceiver()
        node = StubNode(receiver, path)

        node.setTree(tree)

        self.assertEqual(receiver.treeCalls, [(tree, path)])

    def test_AcceptAppendsPath(self):
        tree = SampleTree([])
        receiver = StubReceiver()
        node = StubNode(receiver, Path.of("a"))

        node.accept(tree, Path.of("b", "c"))

        self.assertEqual(
            receiver.treeCalls,
            [(tree, Path.of("a", "b", "c"))],
        )

    def test_ChildReceiverCreatesDefaultNode(self):
        receiver = StubReceiver()
        node = StubNode(receiver, Path.of("a"))

        child = node.childReceiver("b")

        self.assertIsInstance(child, DefaultReceiverNode)
        self.assertIs(child.receiver(), receiver)
        self.assertEqual(child.path(), Path.of("a", "b"))

    def test_IntChildCreatesTypedNode(self):
        receiver = StubReceiver()
        node = StubNode(receiver, Path.of("a"))

        child = node.intChild("b")

        self.assertIsInstance(child, DefaultIntReceiverNode)
        self.assertIs(child.receiver(), receiver)
        self.assertEqual(child.path(), Path.of("a", "b"))


    def test_DoubleChildCreatesTypedNode(self):
        receiver = StubReceiver()
        node = StubNode(receiver, Path.of("a"))

        child = node.doubleChild("b")

        self.assertIsInstance(child, DefaultDoubleReceiverNode)
        self.assertIs(child.receiver(), receiver)
        self.assertEqual(child.path(), Path.of("a", "b"))

    def test_StringChildCreatesTypedNode(self):
        receiver = StubReceiver()
        node = StubNode(receiver, Path.of("a"))

        child = node.stringChild("b")

        self.assertIsInstance(child, DefaultStringReceiverNode)
        self.assertIs(child.receiver(), receiver)
        self.assertEqual(child.path(), Path.of("a", "b"))

    def test_DataChildCreatesTypedNode(self):
        receiver = StubReceiver()
        node = StubNode(receiver, Path.of("a"))

        child = node.dataChild("b")

        self.assertIsInstance(child, DefaultDataReceiverNode)
        self.assertIs(child.receiver(), receiver)
        self.assertEqual(child.path(), Path.of("a", "b"))

    def test_PathChildCreatesTypedNode(self):
        receiver = StubReceiver()
        node = StubNode(receiver, Path.of("a"))

        child = node.pathChild("b")

        self.assertIsInstance(child, DefaultPathReceiverNode)
        self.assertIs(child.receiver(), receiver)
        self.assertEqual(child.path(), Path.of("a", "b"))