import unittest

from soil.data import Path, Sample, SampleTree, Timestamp
from soil.data.value import Value
from soil.messaging.message import Message
from soil.messaging.message_type import MessageType


class TestMessage(unittest.TestCase):

    # MARK: Defaults

    def test_Defaults(self):
        message = Message()

        self.assertEqual(message.type, MessageType.DATA)
        self.assertTrue(message.path.isEmpty)
        self.assertTrue(message.data.isEmpty)
        self.assertIsNone(message.count)
        self.assertIsNone(message.depth)
        self.assertIsNone(message.time)
        self.assertIsNone(message.end)
        self.assertIsNone(message.id)

    # MARK: Factories

    def test_Acknowledge(self):
        path = Path.of("a")
        ts = Timestamp.current()

        message = Message.acknowledge(7, path, ts)

        self.assertEqual(message.type, MessageType.DATA)
        self.assertEqual(message.path, path)
        self.assertEqual(message.time, ts)
        self.assertEqual(message.id, 7)
        self.assertTrue(message.data.isEmpty)

    def test_Value(self):
        path = Path.of("a")
        ts = Timestamp.current()

        message = Message.value(Value(42), path, ts, request=3, totalMessages=5)

        self.assertEqual(message.type, MessageType.DATA)
        self.assertEqual(message.path, path)
        self.assertEqual(message.count, 5)
        self.assertEqual(message.id, 3)
        self.assertFalse(message.data.isEmpty)

    def test_Samples(self):
        path = Path.of("a")
        samples = [Sample(Value(1)), Sample(Value(2))]

        message = Message.samples(samples, path, request=3, totalMessages=5)

        self.assertEqual(message.type, MessageType.DATA)
        self.assertEqual(message.path, path)
        self.assertEqual(message.count, 5)
        self.assertEqual(message.id, 3)

    def test_Tree(self):
        path = Path.of("a")
        tree = SampleTree([Sample(Value(1))])

        message = Message.tree(tree, path, request=3, totalMessages=5)

        self.assertEqual(message.type, MessageType.DATA)
        self.assertIs(message.data, tree)
        self.assertEqual(message.count, 5)
        self.assertEqual(message.id, 3)

    def test_Request(self):
        path = Path.of("a")
        start = Timestamp.current()
        end = Timestamp.current()

        message = Message.request(path, start, end, limit=10, depth=2, id=5)

        self.assertEqual(message.type, MessageType.REQUEST)
        self.assertEqual(message.path, path)
        self.assertEqual(message.time, start)
        self.assertEqual(message.end, end)
        self.assertEqual(message.count, 10)
        self.assertEqual(message.depth, 2)
        self.assertEqual(message.id, 5)

    def test_Delete(self):
        path = Path.of("a")
        start = Timestamp.current()
        end = Timestamp.current()

        message = Message.delete(path, start, end, depth=2, id=5)

        self.assertEqual(message.type, MessageType.DELETION)
        self.assertEqual(message.path, path)
        self.assertEqual(message.time, start)
        self.assertEqual(message.end, end)
        self.assertEqual(message.depth, 2)
        self.assertEqual(message.id, 5)

    def test_Include(self):
        message = Message.include(Path.of("a"), depth=2)

        self.assertEqual(message.type, MessageType.SUBSCRIPTION_INCLUSION)
        self.assertEqual(message.path, Path.of("a"))
        self.assertEqual(message.depth, 2)

    def test_Exclude(self):
        message = Message.exclude(Path.of("a"), depth=2)

        self.assertEqual(message.type, MessageType.SUBSCRIPTION_EXCLUSION)
        self.assertEqual(message.path, Path.of("a"))
        self.assertEqual(message.depth, 2)

    def test_DeleteRules(self):
        message = Message.deleteRules(Path.of("a"), depth=2)

        self.assertEqual(message.type, MessageType.SUBSCRIPTION_DELETION)
        self.assertEqual(message.path, Path.of("a"))
        self.assertEqual(message.depth, 2)

    # MARK: String

    def test_StrContainsAllFields(self):
        message = Message.request(
            Path.of("a", "b"),
            Timestamp.current(),
            depth=2,
            id=5,
        )

        text = str(message)

        self.assertIn("type: read", text)
        self.assertIn("path: a > b", text)
        self.assertIn("depth: 2", text)
        self.assertIn("id: 5", text)
        self.assertIn("time:", text)

    def test_StrOmitsEmptyFields(self):
        message = Message()

        text = str(message)

        self.assertIn("type: data", text)
        self.assertNotIn("path:", text)
        self.assertNotIn("count:", text)
        self.assertNotIn("id:", text)
        self.assertNotIn("data:", text)

    def test_StrContainsData(self):
        message = Message.value(Value(42), Path.of("a"))

        text = str(message)

        self.assertIn("data:", text)

    # MARK: Equality

    def test_Equal(self):
        a = Message.include(Path.of("a"), depth=2)
        b = Message.include(Path.of("a"), depth=2)

        self.assertEqual(a, b)

    def test_NotEqualType(self):
        a = Message.include(Path.of("a"))
        b = Message.exclude(Path.of("a"))

        self.assertNotEqual(a, b)

    def test_NotEqualPath(self):
        a = Message.include(Path.of("a"))
        b = Message.include(Path.of("b"))

        self.assertNotEqual(a, b)

    def test_NotEqualTimeNone(self):
        ts = Timestamp.current()
        a = Message.request(Path.of("a"), start=ts)
        b = Message.request(Path.of("a"), start=None)

        self.assertNotEqual(a, b)
        self.assertNotEqual(b, a)

    def test_EqualWithSameTimestamp(self):
        ts = Timestamp.current()
        a = Message.request(Path.of("a"), start=ts)
        b = Message.request(Path.of("a"), start=ts)

        self.assertEqual(a, b)

    def test_NotEqualWithOtherType(self):
        message = Message()

        self.assertFalse(message == "kein Message")
        self.assertTrue(message != "kein Message")


    def test_StrContainsCountAndEnd(self):
        end = Timestamp.current()
        message = Message.request(Path.of("a"), end=end, limit=3)

        text = str(message)

        self.assertIn("count: 3", text)
        self.assertIn("end:", text)