from unittest import TestCase, main

from soil.data.immutable_tree import ImmutableSampleTree
from soil.messaging import Message, MessageType
from soil.data import Path, Sample, Timestamp, Value
from soil.encoding.json import JsonEncoding


class JsonTests(TestCase):

    def _roundTrip(self, message: Message) -> Message:
        encoding = JsonEncoding()

        data = encoding.encode(message)
        decoded = encoding.decode(data)

        if decoded == message:
            return decoded

        print(message)
        print(data.decode())
        print(decoded)
        self.fail("Decoded message doesn't match the original")

    def testBasicValueMessage(self):
        message = Message.value(Value(123), Path.of("some", "path"), Timestamp.current())
        self._roundTrip(message)

    def testMultipleSamples(self):
        now = Timestamp.current()
        samples = [Sample(Value(123), now), Sample(Value(3.14), now.adding(10.0))]
        message = Message.samples(samples, Path.of("some", "path"))
        self._roundTrip(message)

    def testMessageWithData(self):
        data = b'hello'
        message = Message.value(Value(data), Path.of("more", "data"))
        self._roundTrip(message)

    def testTree(self):
        now = Timestamp.current()
        data = ImmutableSampleTree(
            samples = [Sample(Value("val"), now)],
            children = {
                "child" : ImmutableSampleTree.ofValue(Value(234), now.adding(1.0), {
                    "nested" : ImmutableSampleTree.ofValue(Value(123), now.adding(2.0))
                })
            }
        )
        message = Message.tree(data, Path.of("some", "path"))
        self._roundTrip(message)

    def testDataMessageWithProperties(self):
        message = Message.value(
            value = Value(123),
            path = Path.of("some", "path"),
            timestamp = Timestamp.current(),
            request = 345,
            totalMessages = 456)
        self._roundTrip(message)

    def testRequest(self):
        now = Timestamp.current()
        message = Message.request(
            path = Path.of("a", "b", "c"),
            start = now,
            end = now.adding(3600.0),
            limit = 123,
            depth = 234,
            id = 345)
        self._roundTrip(message)

    def testDeletionMessage(self):
        now = Timestamp.current()
        message = Message.delete(
            path = Path.of("c", "d", "e"),
            start = now,
            end = now.adding(3600.0),
            depth = 234,
            id = 345)
        self._roundTrip(message)

    def testSubscriptionInclusion(self):
        message = Message.include(
            path = Path.of("some", "path"),
            subscription = 123,
            depth = 234
        )
        self._roundTrip(message)

    def testSubscriptionExclusion(self):
        message = Message.exclude(
            path = Path.of("some", "path"),
            subscription = 123,
            depth = 234
        )
        self._roundTrip(message)

    def testSubscriptionRuleDeletion(self):
        message = Message.deleteRules(
            path = Path.of("some", "path"),
            subscription = 123,
            depth = 234
        )
        self._roundTrip(message)

    def testEmptyJson(self):
        data = b'{}'
        decoded = JsonEncoding().decode(data)
        expected = Message(type=MessageType.DATA, path=Path())
        self.assertEqual(decoded, expected)


if __name__ == "__main__":
    main()
