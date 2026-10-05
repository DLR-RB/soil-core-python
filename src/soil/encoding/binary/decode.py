from struct import unpack

from ...data import Path, Sample, SampleTree, Timestamp, Value, ValueType
from ...messaging import Message, MessageType


def decodeMessage(data: bytes) -> Message:
    if len(data) == 0:
        return Message()
    buffer = MessageDecoder(data)
    return buffer.decode()


class MessageDecoder:

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.index = 0
        self.total = len(data)

    def decode(self) -> Message:
        firstByte = self.nextByte()
        type = _decodeMessageType(firstByte >> 5)

        if type == MessageType.DATA:
            return self._decodeDataMessage(firstByte)
        return self.decodeNonDataMessage(type, firstByte)

    def nextByte(self) -> int:
        if self.index >= self.total:
            raise ValueError(f"Insufficient bytes ({self.total})")
        byte = self.data[self.index]
        self.index += 1
        return byte

    def nextBytes(self, count: int) -> bytes:
        newIndex = self.index + count
        if newIndex > self.total:
            raise ValueError(f"Insufficient bytes: {self.total} total, needed {count}, had {self.total - self.index}")
        result = self.data[self.index:newIndex]
        self.index = newIndex
        return result

    def _decodeDataMessage(self, firstByte: int) -> Message:
        id = self.decodeOptionalInt(firstByte, 4)
        count = self.decodeOptionalInt(firstByte, 3)
        path, data = self.decodeTree().containedTree()
        return Message(
            path = path,
            data = data,
            count = count,
            id = id
        )

    def decodeNonDataMessage(self, type: MessageType, firstByte: int) -> Message:
        id = self.decodeOptionalInt(firstByte, 4)
        count = self.decodeOptionalInt(firstByte, 3)
        depth = self.decodeOptionalInt(firstByte, 2)
        time = self.decodeOptionalTime(firstByte, 1)
        end = self.decodeOptionalTime(firstByte, 0)
        path = self.decodePath()
        return Message(
            type = type,
            path = path,
            count = count,
            depth = depth,
            time = time,
            end = end,
            id = id
        )

    def decodeOptionalInt(self, byte: int, bit: int) -> int | None:
        if byte & (1 << bit):
            return self.decodeUnsignedInt()
        return None

    def decodeOptionalTime(self, byte: int, bit: int) -> Timestamp | None:
        if byte & (1 << bit):
            return self.decodeTime()
        return None

    def decodeUnsignedInt(self) -> int:
        value = 0
        for shift in range(0, 49, 7):
            byte = self.nextByte()
            bits = byte & 0b01111111
            value |= (bits << shift)
            if not (byte & (1 << 7)):
                return value
        byte = self.nextByte()
        value |= (byte << 56)
        return value

    def decodeSignedInt(self) -> int:
        raw = self.decodeUnsignedInt()
        if raw % 2 == 0:
            return raw >> 1
        return -((raw + 1) >> 1)

    def decodeTime(self) -> Timestamp:
        raw = self.decodeDouble()
        return Timestamp.fromTimeIntervalSince1970(raw)

    def decodeDouble(self) -> float:
        raw = self.nextBytes(8)
        return unpack(">d", raw)[0]

    def decodeString(self) -> str:
        raw = self.decodeData()
        return raw.decode()

    def decodeData(self) -> bytes:
        length = self.decodeUnsignedInt()
        return self.nextBytes(length)

    def decodePath(self) -> Path:
        count = self.decodeUnsignedInt()
        components = [self.decodeString() for _ in range(count)]
        return Path(components)

    def decodeList(self) -> list[Value]:
        count = self.decodeUnsignedInt()
        return [self.decodeTypedValue() for _ in range(count)]

    def decodeMap(self) -> dict[str, Value]:
        count = self.decodeUnsignedInt()
        entries: dict[str, Value] = dict()
        for _ in range(count):
            key = self.decodeString()
            entries[key] = self.decodeTypedValue()
        return entries

    def decodeTypedValue(self) -> Value:
        type = _decodeValueType(self.nextByte())
        return self.decodeValue(type)

    def decodeTree(self) -> SampleTree:
        firstByte = self.nextByte()
        childCount = firstByte >> 4
        if childCount == 0b1111:
            childCount = self.decodeUnsignedInt()
        sampleCount = firstByte & 0b1111
        if sampleCount == 0b1111:
            sampleCount = self.decodeUnsignedInt()
        samples = [self.decodeSample() for _ in range(sampleCount)]
        children: dict[str, SampleTree] = dict()
        for _ in range(childCount):
            name = self.decodeString()
            child = self.decodeTree()
            children[name] = child
        return SampleTree(samples, children)

    def decodeSample(self) -> Sample:
        firstByte = self.nextByte()
        type = _decodeValueType(firstByte & 0b01111111)
        timestamp = self.decodeOptionalTime(firstByte, 7)
        value = self.decodeValue(type)
        return Sample(value, timestamp)

    def decodeValue(self, type: ValueType) -> Value:
        value: int | str | float | bytes | Path | list[Value] | dict[str, Value] | None = None
        match type:
            case ValueType.NONE: pass
            case ValueType.INTEGER: value = self.decodeSignedInt()
            case ValueType.DOUBLE: value = self.decodeDouble()
            case ValueType.STRING: value = self.decodeString()
            case ValueType.DATA: value = self.decodeData()
            case ValueType.PATH: value = self.decodePath()
            case ValueType.LIST: value = self.decodeList()
            case ValueType.MAP: value = self.decodeMap()
            case _:
                raise ValueError(f"Unknown value type ({type})")
        return Value(value)

# MARK: Message type

def _decodeMessageType(raw: int) -> MessageType:
    """ Encode the message type """
    match raw:
        case 0: return MessageType.DATA
        case 1: return MessageType.REQUEST
        case 2: return MessageType.DELETION
        case 3: return MessageType.SUBSCRIPTION_INCLUSION
        case 4: return MessageType.SUBSCRIPTION_EXCLUSION
        case 5: return MessageType.SUBSCRIPTION_DELETION
        case _: raise ValueError(f"Unknown message type ({raw})")

# MARK: Value type

def _decodeValueType(raw: int) -> ValueType:
    match raw:
        case 0: return ValueType.NONE
        case 1: return ValueType.INTEGER
        case 2: return ValueType.DOUBLE
        case 3: return ValueType.STRING
        case 4: return ValueType.DATA
        case 5: return ValueType.PATH
        case 6: return ValueType.LIST
        case 7: return ValueType.MAP
        case _: raise ValueError(f"Unknown value type ({raw})")
