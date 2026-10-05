from unittest import TestCase

from soil.data import Path, Sample, Timestamp, Value, ValueType
from soil.data.sampletree import SampleTree
from soil.encoding.json.min import (
    CompactJsonEncoding,
    JsonKey,
    _convertJsonToMessage,
    _convertMessageToDict,
    _createPathFromList,
    _decodeChildren,
    _decodeInt,
    _decodeMessageType,
    _decodeMessageTypeField,
    _decodePath,
    _decodeSample,
    _decodeSampleFromListElement,
    _decodeSamples,
    _decodeTime,
    _decodeTimestamp,
    _decodeTree,
    _decodeValue,
    _decodeValueType,
    _decodeValueWithType,
    _encodeMessageType,
    _encodeSample,
    _encodeSampleToContainer,
    _encodeTree,
    _encodeValueInContainer,
    _encodeValueType,
)
from soil.messaging import Message, MessageType


class TestJsonKey(TestCase):
    def test_values(self):
        self.assertEqual(JsonKey.MESSAGE_TYPE, "m")
        self.assertEqual(JsonKey.COUNT, "c")
        self.assertEqual(JsonKey.DEPTH, "d")
        self.assertEqual(JsonKey.TIME, "t")
        self.assertEqual(JsonKey.END, "e")
        self.assertEqual(JsonKey.ID, "i")
        self.assertEqual(JsonKey.CHILDREN, "n")
        self.assertEqual(JsonKey.SAMPLES, "s")
        self.assertEqual(JsonKey.VALUE, "v")
        self.assertEqual(JsonKey.VALUE_TYPE, "h")
        self.assertEqual(JsonKey.PATH, "p")



class TestCompactJsonEncoding(TestCase):
    def setUp(self):
        self.enc = CompactJsonEncoding()

    def test_roundtrip_simple_int(self):
        msg = Message(MessageType.DATA, Path(), SampleTree([Sample(Value(42), None)], {}))
        raw = self.enc.encode(msg)
        result = self.enc.decode(raw)

        self.assertEqual(result.type, MessageType.DATA)
        self.assertEqual(result.data.samples[0].value, Value(42))


    def test_roundtrip_string(self):
        msg = Message(MessageType.DATA, Path(), SampleTree([Sample(Value("hello"), None)], {}))
        result = self.enc.decode(self.enc.encode(msg))

        self.assertEqual(result.data.samples[0].value, Value("hello"))


    def test_roundtrip_path(self):
        p = Path.of("a", "b")
        msg = Message(MessageType.DATA, p, SampleTree([Sample(Value(1), None)], {}))
        result = self.enc.decode(self.enc.encode(msg))

        self.assertEqual(result.path, p)


    def test_roundtrip_bytes(self):
        raw_bytes = b"\x01\x02\x03"
        msg = Message(MessageType.DATA, Path(), SampleTree([Sample(Value(raw_bytes), None)], {}))
        result = self.enc.decode(self.enc.encode(msg))

        self.assertEqual(result.data.samples[0].value, Value(raw_bytes))


    def test_roundtrip_multiple_samples(self):
        tree = SampleTree([Sample(Value(1), None), Sample(Value(2), None)], {})
        msg = Message(MessageType.DATA, Path(), tree)
        result = self.enc.decode(self.enc.encode(msg))

        self.assertEqual(len(result.data.samples), 2)


    def test_roundtrip_non_data_message_type(self):
        msg = Message(MessageType.REQUEST, Path(), SampleTree([], {}))
        result = self.enc.decode(self.enc.encode(msg))

        self.assertEqual(result.type, MessageType.REQUEST)


# tbc if new features for convertible are implemented