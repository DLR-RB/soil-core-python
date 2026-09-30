import unittest

from soil.components import Receiver
from soil.data import ImmutableSampleTree, Path, Sample, SampleTree, Timestamp, Value


class TestReceiverInterfaceLogic(unittest.TestCase):

    def test_receiver_interface_logic(self):
        
        fake_receiver = MyTestReceiver()

        ts = Timestamp.current()
        sample = Sample(Value(50), ts)
        tree_to_send = ImmutableSampleTree.create(samples=[sample])

        fake_receiver.accept(tree_to_send, Path.of("test"))

        self.assertTrue(fake_receiver.received_data, "Der Fake-Empfänger wurde nicht aufgerufen!")
        
        received_tree = fake_receiver.last_received_tree
        self.assertEqual(received_tree, tree_to_send)


class MyTestReceiver(Receiver):
    def __init__(self):
        self.received_data = False
        self.last_received_tree = None

    def accept(self, tree: SampleTree, path) -> None:
        self.received_data = True
        self.last_received_tree = tree