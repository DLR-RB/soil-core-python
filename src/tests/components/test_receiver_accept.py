import unittest

from soil.components import Receiver
from soil.data import Path, Sample, SampleTree, Timestamp, Value
from soil.logging import LogLevel
from soil.logging.default import DefaultLogger


class TestReceiverInterfaceLogic(unittest.TestCase):

    def test_receiver_interface_logic(self):
        
        fake_receiver = MyTestReceiver()

        ts = Timestamp.current()
        sample = Sample(Value(50), ts)
        tree_to_send = SampleTree.create(samples=[sample])

        fake_receiver.accept(tree_to_send, Path.of("test"))

        self.assertTrue(fake_receiver.received_data, "Der Fake-Empfänger wurde nicht aufgerufen!")
        
        received_tree = fake_receiver.last_received_tree
        self.assertEqual(received_tree, tree_to_send)
        self.assertEqual(fake_receiver.last_path, Path.of("test"))


    def test_acceptRootTree(self):
        fake_receiver = MyTestReceiver()

        ts = Timestamp.current()
        sample = Sample(Value(50), ts)
        tree_to_send = SampleTree.create(samples=[sample])  

        fake_receiver.acceptRootTree(tree_to_send)

        self.assertEqual(fake_receiver.last_received_tree, tree_to_send)
        self.assertEqual(fake_receiver.last_path, Path())


    def test_logger(self):
        fake_receiver = MyTestReceiver()
        path = Path.of("app", "logs")
        logger = fake_receiver.loggerAtPath(LogLevel.DEBUG, path)
        logger1 = fake_receiver.logger(LogLevel.INFO, "a", "b")
        
        self.assertIsInstance(logger, DefaultLogger)
        self.assertIsInstance(logger1, DefaultLogger)
        


class MyTestReceiver(Receiver):
    def __init__(self):
        self.received_data = False
        self.last_received_tree = None
        self.last_path = Path()
        self.log = None

    def accept(self, tree: SampleTree, path) -> None:
        self.received_data = True
        self.last_received_tree = tree
        self.last_path = path