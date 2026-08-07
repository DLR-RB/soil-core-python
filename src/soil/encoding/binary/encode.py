from struct import pack

from ...data import Path, Sample, SampleTree, Timestamp, Value, ValueType
from ...messaging import Message, MessageType

def encodeMessage(message: Message) -> bytes:
    """
    Convert a message to binary data for transmission.

    Parameters:
        message (Message):
            The message to encode

    Returns:
        (bytes)
            The binary data of the encoded message
    """
    return MessageEncoder().encode(message)


class MessageEncoder:

    def __init__(self) -> None:
        self.buffer = bytearray()

    @property
    def bytes(self) -> bytes:
        return bytes(self.buffer)

    def encode(self, message: Message) -> bytes:
        if message.type == MessageType.DATA:
            self.encodeDataMessage(message)
        else:
            self.encodeNonDataMessage(message)
        return self.bytes

    def encodeDataMessage(self, message: Message) -> None:
        self.encodeTypeIdCount(message)
        self.encodeTopLevelPath(message.path)
        self.encodeTree(message.data)

    def encodeNonDataMessage(self, message: Message) -> None:
        self.encodeTypeIdCount(message)
        if message.depth is not None:
            self.buffer[0] |= (1 << 2) # Set the DEPTH indicator bit
            self.encodeUnsignedInt(message.depth)
        if message.time is not None:
            self.buffer[0] |= (1 << 1) # Set the TIME indicator bit
            self.encodeTime(message.time)
        if message.end is not None:
            self.buffer[0] |= (1 << 0) # Set the END indicator bit
            self.encodeTime(message.end)
        self.encodePath(message.path)

    def encodeTypeIdCount(self, message: Message) -> None:
        """
        Encode the message type, request id, and count, which are shared among all message types.
        """
        firstByte = encodeMessageType(message.type) << 5
        self.buffer.append(firstByte)
        if message.id is not None:
            self.buffer[0] |= (1 << 4) # Set the ID indicator bit
            self.encodeUnsignedInt(message.id)
        if message.count is not None:
            self.buffer[0] |= (1 << 3) # Set the COUNT indicator bit
            self.encodeUnsignedInt(message.count)
        #

    def encodeUnsignedInt(self, value: int) -> None:
        """
        Encode a 64-bit unsigned integer using base-128 encoding.

        Bytes 1-8:
            bit 7 = continuation flag
            bits 0-6 = data
        Byte 9:
            all 8 bits = data
        """
        if value < 0:
            self.buffer.append(0)
            return
        elif value > 0xFFFFFFFFFFFFFFFF:
            self.buffer += b"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF"
            return

        # Emit up to 8 continuation bytes (7 bits each)
        for _ in range(8):
            bits = value & 0x7F
            value >>= 7

            if value == 0:
                self.buffer.append(bits)
                return

            self.buffer.append(bits | 0x80)

        # Remaining 8 bits (no continuation flag)
        self.buffer.append(value)

    def encodeSignedInt(self, value: int) -> None:
        """
        Encode a signed integer as a ZigZag VarInt.

        Positive integers p are encoded as `2 * p` (the even numbers), while negative integers `n` are encoded as `2 * |n| - 1` (the odd numbers).
        """
        value *= 2
        if value >= 0:
            self.encodeUnsignedInt(value)
        else:
            self.encodeUnsignedInt(-value - 1)

    def encodeDouble(self, value: float) -> None:
        encoded = pack(">d", value)
        self.buffer.extend(encoded)

    def encodeTime(self, value: Timestamp) -> None:
        self.encodeDouble(value.timeIntervalSince1970)

    def encodeString(self, value: str) -> None:
        self.encodeData(value.encode())

    def encodeData(self, value: bytes) -> None:
        self.encodeUnsignedInt(len(value))
        self.buffer.extend(value)

    def encodePath(self, value: Path) -> None:
        self.encodeUnsignedInt(len(value)) # Encode the number of components
        for component in value:
            self.encodeString(component)

    def encodeTopLevelPath(self, path: Path) -> None:
        """ Encode the top level path like a tree with no samples and only one child each """
        for component in path:
            headerByte = (1 << 4) # One child, no samples
            self.buffer.append(headerByte)
            self.encodeString(component) # Add the name

    def encodeTree(self, tree: SampleTree) -> None:
        headerIndex = len(self.buffer)
        samples = tree.samples
        sampleCount = len(samples)
        children = tree.children
        childCount = len(children)
        self.buffer.append(0)
        if childCount < 15:
            self.buffer[headerIndex] |= childCount << 4 # Set the child count for the first 4 bits
        else:
            self.buffer[headerIndex] |= 0b11110000 # Set the CHILD_COUNT to max, indicating the presence of EXTENDED_CHILD_COUNT
            self.encodeUnsignedInt(childCount)
        if sampleCount < 15:
            self.buffer[headerIndex] |= sampleCount
        else:
            self.buffer[headerIndex] |= 0b1111 # Set the SAMPLE_COUNT to max, indicating the presence of EXTENDED_SAMPLE_COUNT
            self.encodeUnsignedInt(sampleCount)
        for sample in samples:
            self.encodeSample(sample)
        for name, child in children.items():
            self.encodeString(name)
            self.encodeTree(child)
        #

    def encodeSample(self, sample: Sample) -> None:
        value = sample.value
        firstByte = encodeValueType(value.type)
        if sample.timestamp is not None:
            firstByte |= (1 << 7) # Set the timestamp indicator
            self.buffer.append(firstByte)
            self.encodeTime(sample.timestamp)
        else:
            self.buffer.append(firstByte)
        self.encodeValue(value)

    def encodeValue(self, value: Value) -> None:
        val = value.value
        match val:
            case None: pass
            case int(x): self.encodeSignedInt(x)
            case float(x): self.encodeDouble(x)
            case str(x): self.encodeString(x)
            case bytes(x): self.encodeData(x)
            case Path(x): self.encodePath(x)

    # MARK: Message type

def encodeMessageType(type: MessageType) -> int:
    """ Encode the message type """
    match type:
        case MessageType.DATA: return 0
        case MessageType.REQUEST: return 1
        case MessageType.DELETION: return 2
        case MessageType.SUBSCRIPTION_INCLUSION: return 3
        case MessageType.SUBSCRIPTION_EXCLUSION: return 4
        case MessageType.SUBSCRIPTION_DELETION: return 5

# MARK: Value type

def encodeValueType(type: ValueType) -> int:
    match type:
        case ValueType.NONE: return 0
        case ValueType.INTEGER: return 1
        case ValueType.DOUBLE: return 2
        case ValueType.STRING: return 3
        case ValueType.DATA: return 4
        case ValueType.PATH: return 5
