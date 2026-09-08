import unittest
from soil.data import Path, Sample, Value, ImmutableSampleTree, Timestamp, SampleTree
from soil.components import Receiver

def test_receiver_interface_logic(self):
        
        fake_receiver = MyTestReceiver()

        ts = Timestamp.current()
        sample = Sample(Value(50), ts)
        tree_to_send = ImmutableSampleTree.create(samples=[sample])

        request = fake_receiver.accept(tree_to_send, Path.of("test"))

        self.assertTrue(fake_receiver.received_data, "Der Fake-Empfänger wurde nicht aufgerufen!")
        
        received_tree = fake_receiver.last_received_tree
        self.assertEqual(received_tree, 1)


class MyTestReceiver(Receiver):
    def __init__(self):
        self.received_data = False
        self.last_received_tree = None

    def accept(self, tree: SampleTree, path) -> None:
        self.received_data = True
        self.last_received_tree = tree