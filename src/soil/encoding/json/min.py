from base64 import b64decode, b64encode
from enum import StrEnum
from json import dumps, loads
from typing import Any, override

from soil.data.path import Path
from soil.data.sampletree import SampleTree
from soil.data.timestamp import Timestamp
from soil.data.type import ValueType

from ...data.sample import Sample
from ...data.value import Value
from ...messaging.encoding import MessageEncoding
from ...messaging.message import Message
from ...messaging.message_type import MessageType


class JsonKey(StrEnum):
    MESSAGE_TYPE = "m"
    COUNT = "c"
    DEPTH = "d"
    TIME = "t"
    END = "e"
    ID = "i"
    CHILDREN = "n"
    SAMPLES = "s"
    VALUE = "v"
    VALUE_TYPE = "h" # "h" for  type "hint"
    PATH = "p"


class CompactJsonEncoding(MessageEncoding):

    @override
    def encode(self, message: Message) -> bytes:
        converted = _convertMessageToDict(message)
        return dumps(converted).encode("utf-8")

    @override
    def decode(self, data: bytes) -> Message:
        raw = loads(data)
        return _convertJsonToMessage(raw)

# MARK: Encoding

def _convertMessageToDict(message: Message) -> dict[str, Any]:
    result:  dict[str, Any] = dict()
    # Only encode message type if not a data message
    if message.type != MessageType.DATA:
        result[JsonKey.MESSAGE_TYPE] = _encodeMessageType(message.type)
    # If the path is absent, then it defaults to an empty path
    if not message.path.isEmpty:
        result[JsonKey.PATH] = message.path

    # There is a possibly invalid message where the `time` is set in addition to data being present
    # We ensure that the timestamp is not written into the message if any samples are provided
    # so that decoding does not fail
    _encodeTree(message.data, result, message.time is None)

    if message.count is not None:
        result[JsonKey.COUNT] = message.count
    if message.depth is not None:
        result[JsonKey.DEPTH] = message.depth
    if message.time is not None:
        result[JsonKey.TIME] = message.time.timeIntervalSince1970 # time since 1970
    if message.end is not None:
        result[JsonKey.END] = message.end.timeIntervalSince1970
    if message.id is not None:
        result[JsonKey.ID] = message.id

    return result

def _encodeTree(tree: SampleTree, container: dict[str, Any], canUseRoot: bool) -> None:
    samples = tree.samples
    if len(samples) == 1 and canUseRoot:
        # Encode a single sample at the top-level of the container,
        # but only if the 'time' field is not already used
        _encodeSampleToContainer(samples[0], container)
    elif len(samples) > 1:
        container[JsonKey.SAMPLES] = [_encodeSample(s) for s in samples]

    children = tree.children
    if len(children) == 0:
        return
    childList: dict[str, Any] = dict()
    for name, child in children.items():
        childContainer: dict[str, Any] = dict()
        _encodeTree(child, childContainer, canUseRoot=True)
        childList[name] = childContainer
    container[JsonKey.CHILDREN] = childList

def _encodeValueInContainer(value: Value, container: dict[str, Any]) -> None:
    type = value.type
    if type == ValueType.DATA:
        container[JsonKey.VALUE_TYPE] = str(type)
        rawBytes: bytes = value.value # pyright: ignore[reportAssignmentType]
        container[JsonKey.VALUE] = b64encode(rawBytes).decode('ascii')
        return
    if type == ValueType.INTEGER:
        container[JsonKey.VALUE_TYPE] = _encodeValueType(type)
    container[JsonKey.VALUE] = value.value

def _encodeSample(sample: Sample) -> dict[str, Any]:
    container: dict[str, Any] = dict()
    _encodeSampleToContainer(sample, container)
    return container

def _encodeSampleToContainer(sample: Sample, container: dict[str, Any]) -> None:
    _encodeValueInContainer(sample.value, container)
    if sample.timestamp is not None:
        container[JsonKey.TIME] = sample.timestamp.timeIntervalSince1970

# MARK: Decoding

def _convertJsonToMessage(raw: Any) -> Message:
    if not isinstance(raw, dict):
        raise ValueError("Top-level JSON is not a dict")
    container: dict[str, Any] = raw # pyright: ignore[reportUnknownVariableType]
    type = _decodeMessageTypeField(container)
    path = _decodePath(container)
    count = _decodeInt(container, JsonKey.COUNT)
    depth = _decodeInt(container, JsonKey.DEPTH)
    time = _decodeTime(container)
    end = _decodeTimestamp(container, JsonKey.END)
    id = _decodeInt(container, JsonKey.ID)
    data = _decodeTree(container)

    return Message(type, path, data, count, depth, time, end, id)

def _decodeMessageTypeField(container: dict[str, Any]) -> MessageType:
    rawType = container.get(JsonKey.MESSAGE_TYPE)
    if rawType is None:
        return MessageType.DATA
    if not isinstance(rawType, int):
        raise ValueError("Message type is not a integer")
    return _decodeMessageType(rawType)

def _decodePath(container: dict[str, Any]) -> Path:
    rawPath = container.get('p')
    if rawPath is None:
        return Path()
    if not isinstance(rawPath, list):
        raise ValueError("Message path must be a list of strings")
    return _createPathFromList(rawPath) # pyright: ignore[reportUnknownArgumentType]

def _decodeInt(container: dict[str, Any], key: str) -> int | None:
    raw = container.get(key)
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise ValueError(f"Field '{key}' ({raw}) must be an integer, not bool")
    if not isinstance(raw, int):
        raise ValueError(f"Field '{key}' ({raw}) must be an integer, not {type(raw)}")
    return raw

def _decodeTime(container: dict[str, Any]) -> Timestamp | None:
    if container.get(JsonKey.VALUE) is not None:
        # If a value is present, then the timestamp is decoded as part of the sample
        return None
    return _decodeTimestamp(container, 'time')

def _decodeTimestamp(container: dict[str, Any], key: str) -> Timestamp | None:
    raw = container.get(key)
    if raw is None:
        return None
    # Check boolean, since it is a subclass of int
    if isinstance(raw, float):
        return Timestamp.fromTimeIntervalSince1970(raw)
    if isinstance(raw, int):
        return Timestamp.fromTimeIntervalSince1970(float(raw))
    raise ValueError(f"Field 'time' ({raw}) must be a number, not {type(raw)}")

def _decodeTree(container: dict[str, Any]) -> SampleTree:
    samples = _decodeSamples(container)
    if container.get(JsonKey.VALUE) is not None:
        # Sample present at the top level
        sample = _decodeSample(container)
        samples.append(sample)

    samples.sort()

    children = _decodeChildren(container)
    return SampleTree(samples, children)

def _decodeChildren(container: dict[str, Any]) -> dict[str, SampleTree]:
    raw = container.get(JsonKey.CHILDREN)
    if raw is None:
        return dict()
    if not isinstance(raw, dict):
        raise ValueError(f"Field 'children' must be a dictionary, not {type(raw)}")

    children: dict[str, SampleTree] = dict()
    for name, child in raw.items(): # pyright: ignore[reportUnknownVariableType]
        if not isinstance(name, str):
            raise ValueError(f"Field 'children' must have string keys, not {type(name)}") # pyright: ignore[reportUnknownArgumentType]
        if not isinstance(child, dict):
            raise ValueError(f"Field 'children' must have dictionary values, not {type(child)}")  # pyright: ignore[reportUnknownArgumentType]
        children[name] = _decodeTree(child) # pyright: ignore[reportUnknownArgumentType]
    return children

def _decodeSamples(container: dict[str, Any]) -> list[Sample]:
    raw = container.get(JsonKey.SAMPLES)
    if raw is None:
        return list()
    if not isinstance(raw, list):
        raise ValueError(f"Field 'samples' must be a list, not {type(raw)}")
    return [_decodeSampleFromListElement(e) for e in raw] # pyright: ignore[reportUnknownVariableType]

def _decodeSampleFromListElement(element: Any) -> Sample:
    if not isinstance(element, dict):
        raise ValueError(f'Sample must be represented as a dictionary, not {type(element)}')
    return _decodeSample(element) # pyright: ignore[reportUnknownArgumentType]

def _decodeSample(container: dict[str, Any]) -> Sample:
    value = _decodeValue(container)
    timestamp = _decodeTimestamp(container, 'time')
    return Sample(value, timestamp)

def _decodeValue(container: dict[str, Any]) -> Value:
    rawType = container.get(JsonKey.VALUE_TYPE)
    rawValue = container.get(JsonKey.VALUE)
    if rawType is not None:
        return _decodeValueWithType(rawValue, rawType)
    # Detect the type from the value alone
    if rawValue is None:
        return Value(None)
    if isinstance(rawValue, (float, str)):
        return Value(rawValue)
    if isinstance(rawValue, bool):
        raise ValueError("Value is a boolean")
    if isinstance(rawValue, int):
        return Value(float(rawValue))
    if isinstance(rawValue, list):
        path = _createPathFromList(rawValue) # pyright: ignore[reportUnknownArgumentType]
        return Value(path)
    raise ValueError(f"Field '{JsonKey.VALUE}' has unknown type {type(rawValue)}")


def _decodeValueWithType(rawValue: Any, rawType: Any) -> Value:
    if not isinstance(rawType, int):
        raise ValueError(f"Field '{JsonKey.VALUE_TYPE}' must be an integer, not {type(rawType)}")
    valueType = _decodeValueType(rawType)
    match valueType:
        case ValueType.INTEGER:
            if isinstance(rawValue, bool):
                raise ValueError("Value type declares integer, but value is a boolean")
            if not isinstance(rawValue, int):
                raise ValueError(f"Value type declares integer, but value is {type(rawValue)}")
            return Value(rawValue)
        case ValueType.DOUBLE:
            if isinstance(rawValue, float):
                return Value(rawValue)
            if isinstance(rawValue, bool):
                raise ValueError("Value type declares double, but value is a boolean")
            if isinstance(rawValue, int):
                return Value(float(rawValue))
            raise ValueError(f"Value type declares double, but value is {type(rawValue)}")
        case ValueType.STRING:
            if not isinstance(rawValue, str):
                raise ValueError(f"Value type declares string, but value is {type(rawValue)}")
            return Value(rawValue)
        case ValueType.DATA:
            if not isinstance(rawValue, str):
                raise ValueError(f"Value type declares data, but value is {type(rawValue)}")
            rawBytes = b64decode(rawValue)
            return Value(rawBytes)
        case ValueType.PATH:
            if not isinstance(rawValue, list):
                raise ValueError(f"Value type declares path, but value is {type(rawValue)}")
            path = _createPathFromList(rawValue) # pyright: ignore[reportUnknownArgumentType]
            return Value(path)
        case ValueType.NONE:
            if not rawValue is not None:
                raise ValueError(f"Value type declares null, but value is {type(rawValue)}")
            return Value(None)

def _createPathFromList(rawValue: list[Any]) -> Path:
    for component in rawValue:
        if not isinstance(component, str):
            raise ValueError("Paths must be a list of strings")
    return Path(rawValue)

# MARK: Value type conversion

def _decodeValueType(raw: int) -> ValueType:
    match raw:
        case 0: return ValueType.NONE
        case 1: return ValueType.INTEGER
        case 2: return ValueType.DOUBLE
        case 3: return ValueType.STRING
        case 4: return ValueType.DATA
        case 5: return ValueType.PATH
        case _: raise ValueError(f"Unknown value type {raw}")

def _encodeValueType(type: ValueType) -> int:
    match type:
        case ValueType.NONE: return 0
        case ValueType.INTEGER: return 1
        case ValueType.DOUBLE: return 2
        case ValueType.STRING: return 3
        case ValueType.DATA: return 4
        case ValueType.PATH: return 5

# MARK: Message type

def _decodeMessageType(raw: int) -> MessageType:
    match raw:
        case 0: return MessageType.DATA
        case 1: return MessageType.REQUEST
        case 2: return MessageType.DELETION
        case 3: return MessageType.SUBSCRIPTION_INCLUSION
        case 4: return MessageType.SUBSCRIPTION_EXCLUSION
        case 5: return MessageType.SUBSCRIPTION_DELETION
        case _: raise ValueError(f"Unknown message type {raw}")

def _encodeMessageType(type: MessageType) -> int:
    match type:
        case MessageType.DATA: return 0
        case MessageType.REQUEST: return 1
        case MessageType.DELETION: return 2
        case MessageType.SUBSCRIPTION_INCLUSION: return 3
        case MessageType.SUBSCRIPTION_EXCLUSION: return 4
        case MessageType.SUBSCRIPTION_DELETION: return 5