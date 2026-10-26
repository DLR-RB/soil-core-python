from unittest import TestCase

from soil.data import Path, Sample, Timestamp, Value
from soil.data.sampletree import SampleTree
from soil.encoding.binary import BinaryEncoding
from soil.encoding.binary.decode import MessageDecoder, decodeMessage
from soil.encoding.binary.encode import MessageEncoder
from soil.messaging import Message, MessageType


class BinaryTests(TestCase):

    def _roundTrip(self, message: Message) -> Message:
        encoding = BinaryEncoding()

        data = encoding.encode(message)
        decoded = encoding.decode(data)

        if decoded == message:
            return decoded
        self.fail(f"Decoded message doesn't match the original:\n{message}\n\nis not equal to:\n\n{decoded}")

    def testUnsignedEncoding(self):

        def roundTrip(expected: int):
            encoder = MessageEncoder()
            encoder.encodeUnsignedInt(expected)
            encoded = encoder.bytes
            decoder = MessageDecoder(encoded)
            actual = decoder.decodeUnsignedInt()
            self.assertEqual(expected, actual)

        roundTrip(0)
        roundTrip(123)
        roundTrip(234)
        roundTrip(666666)

        roundTrip(127)
        roundTrip(128)

        roundTrip(16383)
        roundTrip(16384)

        roundTrip(0xFFFFFFFFFFFFFFFF)

    def testSignedEncoding(self):

        def roundTrip(expected: int):
            encoder = MessageEncoder()
            encoder.encodeSignedInt(expected)
            encoded = encoder.bytes
            decoder = MessageDecoder(encoded)
            actual = decoder.decodeSignedInt()
            self.assertEqual(expected, actual)

        roundTrip(0)
        roundTrip(123)
        roundTrip(-123)
        roundTrip(234)
        roundTrip(-234)
        roundTrip(666666)
        roundTrip(-666666)

        roundTrip(127)
        roundTrip(-127)
        roundTrip(128)
        roundTrip(-128)

        roundTrip(16383)
        roundTrip(-16383)
        roundTrip(16384)
        roundTrip(-16384)

        roundTrip(9223372036854775807)
        roundTrip(-9223372036854775808) 


    def testStringEncoding(self):
        expected = "abc"
        encoder = MessageEncoder()
        encoder.encodeString(expected)
        encoded = encoder.bytes
        decoder = MessageDecoder(encoded)
        actual = decoder.decodeString()
        self.assertEqual(expected, actual)

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
        data = SampleTree(
            samples = [Sample(Value("val"), now)],
            children = {
                "child" : SampleTree.ofValue(Value(234), now.adding(1.0), {
                    "nested" : SampleTree.ofValue(Value(123), now.adding(2.0))
                })
            }
        )
        message = Message.tree(data, Path.of("some", "path"))
        self._roundTrip(message)


        now = Timestamp.current()
        data = SampleTree(samples=[Sample(Value(i), now) for i in range(15)])
        message = Message.tree(data, Path.of("some", "path"))
        self._roundTrip(message)

        now = Timestamp.current()
        data = SampleTree(children={
            f"child{i}": SampleTree.ofValue(Value(i), now) for i in range(15)
        })
        message = Message.tree(data, Path.of("some", "path"))
        self._roundTrip(message)

        data = SampleTree()
        message = Message.tree(data, Path.of("some", "path"))
        self._roundTrip(message)

        now = Timestamp.current()
        data = SampleTree(
            samples=[Sample(Value(i), now) for i in range(15)],
            children={
                f"child{i}": SampleTree.ofValue(Value(1000 + i), now) for i in range(15)
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
            depth = 234
        )
        self._roundTrip(message)

    def testSubscriptionExclusion(self):
        message = Message.exclude(
            path = Path.of("some", "path"),
            depth = 234
        )
        self._roundTrip(message)

    def testSubscriptionRuleDeletion(self):
        message = Message.deleteRules(
            path = Path.of("some", "path"),
            depth = 234
        )
        self._roundTrip(message)

    def testEmptyBinary(self):
        data = b''
        decoded = BinaryEncoding().decode(data)
        expected = Message(type=MessageType.DATA, path=Path())
        self.assertEqual(decoded, expected)

    def testPathValueMessage(self):
        message = Message.value(Value(Path.of("a", "b", "c")), Path.of("some", "path"))
        self._roundTrip(message)

    def testNullValueMessage(self):
        message = Message.value(Value(None), Path.of("some", "path"))
        self._roundTrip(message)

    def testPathValue(self):
        self._roundTrip(Message.value(Value(Path.of("x", "y")), Path.of("a")))

    def testNullValue(self):
        self._roundTrip(Message.value(Value(None), Path.of("a")))

    def testListValue(self):
        value = Value([Value(1), Value("a"), Value(Path.of("x"))])
        self._roundTrip(Message.value(value, Path.of("a")))

    def testMapValue(self):
        value = Value({"one": Value(1), "two": Value("zwei")})
        self._roundTrip(Message.value(value, Path.of("a")))

    def testNestedListValue(self):
        value = Value([Value([Value(1), Value("a")]), Value(None)])
        self._roundTrip(Message.value(value, Path.of("a")))

    def testNestedMapValue(self):
        value = Value({"outer": Value({"inner": Value(1)})})
        self._roundTrip(Message.value(value, Path.of("a")))


    def testSingleSampleKeepsItsTimestamp(self):
        ts = Timestamp.current()
        decoded = self._roundTrip(Message.value(Value(123), Path.of("a"), ts))

        self.assertIsNone(decoded.time)
        self.assertEqual(decoded.data.samples[0].timestamp, ts)

    def testEmptyListValue(self):
        self._roundTrip(Message.value(Value([]), Path.of("a")))

    def testEmptyMapValue(self):
        self._roundTrip(Message.value(Value({}), Path.of("a")))

    def testDeeplyNestedListValue(self):
        value = Value([Value([Value([Value(1)])])])
        self._roundTrip(Message.value(value, Path.of("a")))


    def testRejectsTruncatedData(self):
        with self.assertRaises(ValueError):
            decodeMessage(bytes([0b00000001, 0b00000011, 0x05, 0x68, 0x69]))

    def testRejectsInsufficientBytes(self):
        with self.assertRaises(ValueError):
            decodeMessage(bytes([0b00000001]))

    def testRejectsUnknownSampleValueType(self):
        with self.assertRaises(ValueError):
            decodeMessage(bytes([0b00000001, 0b00001000]))

    def testRejectsUnknownMessageType(self):
        with self.assertRaises(ValueError):
            decodeMessage(bytes([0b11100000]))
