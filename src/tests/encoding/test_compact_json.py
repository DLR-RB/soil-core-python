from unittest import TestCase

from soil.data import Path, Sample, Timestamp, Value
from soil.data.sampletree import SampleTree
from soil.encoding.json.min import CompactJsonEncoding
from soil.messaging import Message, MessageType


class CompactJsonTests(TestCase):

    def _roundTrip(self, message: Message) -> Message:
        encoding = CompactJsonEncoding()

        data = encoding.encode(message)
        decoded = encoding.decode(data)

        if decoded == message:
            return decoded

        print(message)
        print(data.decode())
        print(decoded)
        self.fail("Decoded message doesn't match the original")

    def _decode(self, json: str) -> Message:
        return CompactJsonEncoding().decode(json.encode("utf-8"))

    # MARK: Round-Trips

    def testBasicValueMessage(self):
        message = Message.value(Value(123), Path.of("some", "path"), Timestamp.current())
        self._roundTrip(message)

    def testMultipleSamples(self):
        now = Timestamp.current()
        samples = [Sample(Value(123), now), Sample(Value(3.14), now.adding(10.0))]
        self._roundTrip(Message.samples(samples, Path.of("some", "path")))

    def testMessageWithData(self):
        message = Message.value(Value(b'hello'), Path.of("more", "data"))
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
        self._roundTrip(Message.tree(data, Path.of("some", "path")))

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
        self._roundTrip(Message.include(path = Path.of("some", "path"), depth = 234))

    def testSubscriptionExclusion(self):
        self._roundTrip(Message.exclude(path = Path.of("some", "path"), depth = 234))

    def testSubscriptionRuleDeletion(self):
        self._roundTrip(Message.deleteRules(path = Path.of("some", "path"), depth = 234))

    def testEmptyJson(self):
        decoded = self._decode('{}')
        expected = Message(type=MessageType.DATA, path=Path())
        self.assertEqual(decoded, expected)

    # MARK: Neue Value-Typen

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

    # MARK: Compact-Wire-Format

    def testCompactWireFormat(self):
        message = Message.value(Value(123), Path.of("a"))

        data = CompactJsonEncoding().encode(message)
        raw = __import__("json").loads(data)

        self.assertNotIn("valuetype", raw)
        self.assertNotIn("value", raw)
        self.assertEqual(raw["h"], 1)         
        self.assertEqual(raw["v"], 123)
        self.assertEqual(raw["p"], ["a"])
        self.assertNotIn("m", raw)

    def testCompactListWireFormat(self):
        message = Message.value(Value([Value(1), Value("a")]), Path.of("a"))

        data = CompactJsonEncoding().encode(message)
        raw = __import__("json").loads(data)

        self.assertEqual(raw["h"], 6)
        self.assertEqual(raw["v"], [1, 1, 3, "a"]) 

    def testDecodesCompactIntegerValue(self):
        decoded = self._decode('{"p": ["a"], "h": 1, "v": 123}')
        self.assertEqual(decoded.data.samples[0].value.value, 123)

    def testDecodesCompactNullValue(self):
        decoded = self._decode('{"p": ["a"], "h": 0, "v": null}')
        self.assertIsNone(decoded.data.samples[0].value.value)
        self.assertEqual(len(decoded.data.samples), 1)

    def testDecodesCompactMessageType(self):
        decoded = self._decode('{"m": 2, "p": ["gone"]}')
        self.assertEqual(decoded.type, MessageType.DELETION)

    # MARK: Timestamp

    def testSingleSampleKeepsItsTimestamp(self):
        ts = Timestamp.current()
        decoded = self._roundTrip(Message.value(Value(123), Path.of("a"), ts))

        self.assertIsNone(decoded.time)
        self.assertIsNotNone(decoded.data.samples[0].timestamp)

    def testSingleSampleWithMessageTimeKeepsSample(self):
        now = Timestamp.current()
        samples = [Sample(Value(123), now)]
        message = Message(
            type=MessageType.DATA,
            path=Path.of("a"),
            data=SampleTree(samples=samples),
            time=now.adding(10.0))

        decoded = self._roundTrip(message)

        self.assertIsNotNone(decoded.time)
        self.assertEqual(len(decoded.data.samples), 1)
        self.assertEqual(decoded.data.samples[0].timestamp, now)

    # MARK: Fehlerfaelle

    def testRejectsNonDictJson(self):
        with self.assertRaises(ValueError):
            self._decode('[1, 2]')

    def testRejectsUnknownMessageType(self):
        with self.assertRaises(ValueError):
            self._decode('{"m": 99}')

    def testRejectsStringMessageType(self):
        with self.assertRaises(ValueError):
            self._decode('{"m": "deletion"}')

    def testRejectsUnknownValueType(self):
        with self.assertRaises(ValueError):
            self._decode('{"h": 99, "v": 1}')

    def testRejectsStringValueType(self):
        with self.assertRaises(ValueError):
            self._decode('{"h": "integer", "v": 1}')

    def testRejectsBoolAsCount(self):
        with self.assertRaises(ValueError):
            self._decode('{"c": true}')

    def testRejectsOddLengthListValue(self):
        with self.assertRaises(ValueError):
            self._decode('{"h": 6, "v": [1]}')

    def testRejectsShortMapTriple(self):
        with self.assertRaises(ValueError):
            self._decode('{"h": 7, "v": ["key", 1]}')
