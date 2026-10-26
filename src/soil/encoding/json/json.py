from base64 import b64decode, b64encode
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


class JsonEncoding(MessageEncoding):
    """
    JSON wire format for soil messages.
    """

    MSG_TYPE_KEY = "message"
    VALUE_TYPE_KEY = "type"

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
        result[JsonEncoding.MSG_TYPE_KEY] = str(message.type).lower()
    # If the path is absent, then it defaults to an empty path
    if not message.path.isEmpty:
        result["path"] = message.path

    # There is a possibly invalid message where the `time` is set in addition to data being present
    # We ensure that the timestamp is not written into the message if any samples are provided
    # so that decoding does not fail
    _encodeTree(message.data, result, message.time is None)

    if message.count is not None:
        result["count"] = message.count
    if message.depth is not None:
        result["depth"] = message.depth
    if message.time is not None:
        result["time"] = message.time.timeIntervalSince1970 # time since 1970
    if message.end is not None:
        result["end"] = message.end.timeIntervalSince1970
    if message.id is not None:
        result["id"] = message.id

    return result

def _encodeTree(tree: SampleTree, container: dict[str, Any], canUseRoot: bool) -> None:
    samples = tree.samples
    if len(samples) == 1 and canUseRoot:
        # Encode a single sample at the top-level of the container,
        # but only if the 'time' field is not already used
        _encodeSampleToContainer(samples[0], container)
    elif len(samples) >= 1:
        container['samples'] = [_encodeSample(s) for s in samples]

    children = tree.children
    if len(children) == 0:
        return
    childList: dict[str, Any] = dict()
    for name, child in children.items():
        childContainer: dict[str, Any] = dict()
        _encodeTree(child, childContainer, canUseRoot=True)
        childList[name] = childContainer
    container['children'] = childList

def _encodeValueInContainer(value: Value, container: dict[str, Any]) -> None:
    type_val = value.type
    inner = value.value

    container[JsonEncoding.VALUE_TYPE_KEY] = str(type_val).lower()

    if isinstance(inner, bytes):
        container['value'] = b64encode(inner).decode('ascii')
    elif isinstance(inner, Path):
        container['value'] = inner
    elif isinstance(inner, list):
        # Flatten nested values to [type, value, type, value, ...]
        items: list[Any] = []
        for element in inner:
            sub: dict[str, Any] = dict()
            _encodeValueInContainer(element, sub)
            items.append(sub[JsonEncoding.VALUE_TYPE_KEY])
            items.append(sub['value'])
        container['value'] = items
    elif isinstance(inner, dict):
        # Flatten nested values to [key, type, value, ...]
        items = []
        for key, element in inner.items():
            sub: dict[str, Any] = dict()
            _encodeValueInContainer(element, sub)
            items.append(key)
            items.append(sub[JsonEncoding.VALUE_TYPE_KEY])
            items.append(sub['value'])
        container['value'] = items
    else:
        container['value'] = inner

def _encodeSample(sample: Sample) -> dict[str, Any]:
    container: dict[str, Any] = dict()
    _encodeSampleToContainer(sample, container)
    return container

def _encodeSampleToContainer(sample: Sample, container: dict[str, Any]) -> None:
    _encodeValueInContainer(sample.value, container)
    if sample.timestamp is not None:
        container['time'] = sample.timestamp.timeIntervalSince1970

# MARK: Decoding

def _convertJsonToMessage(raw: Any) -> Message:
    if not isinstance(raw, dict):
        raise ValueError("Top-level JSON is not a dict")

    container = raw

    type_msg = _decodeMessageType(container)
    path = _decodePath(container)

    count = _decodeInt(container, 'count')
    depth = _decodeInt(container, 'depth')
    id_ = _decodeInt(container, 'id')

    if 'value' in container:
        time = None
    else:
        time = _decodeTime(container)

    end = _decodeTimestamp(container, 'end')

    # Data decoding consumes the value/type from the root (if present)
    data = _decodeTree(container)

    return Message(type_msg, path, data, count, depth, time, end, id_)

def _decodeMessageType(container: dict[str, Any]) -> MessageType:
    rawType = container.get(JsonEncoding.MSG_TYPE_KEY)
    if rawType is None:
        return MessageType.DATA
    if not isinstance(rawType, str):
        raise ValueError("Message type is not a string")
    return MessageType(rawType)

def _decodePath(container: dict[str, Any]) -> Path:
    rawPath = container.get('path')
    if rawPath is None:
        return Path()

    if isinstance(rawPath, str):
        return Path([rawPath])
    if not isinstance(rawPath, list):
        raise ValueError("Message path must be a list of strings")
    return _createPathFromList(rawPath)

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

    if 'value' in container:
        samples.append(_decodeSample(container))

    samples.sort()
    children = _decodeChildren(container)
    return SampleTree(samples, children)

def _decodeChildren(container: dict[str, Any]) -> dict[str, SampleTree]:
    raw = container.get("children")
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
    raw = container.get('samples')
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
    rawType = container.get(JsonEncoding.VALUE_TYPE_KEY)
    rawValue = container.get('value')
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
        path = _createPathFromList(rawValue) # pyright: ignore[reportUnknownVariableType]
        return Value(path)
    raise ValueError(f"Field 'value' has unknown type {type(rawValue)}")

def _decodeValueWithType(rawValue: Any, rawType: Any) -> Value:
    if not isinstance(rawType, str):
        raise ValueError(f"Field 'valuetype' must be a string, not {type(rawType)}")
    valueType = ValueType(rawType)
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
            try:
                rawBytes = b64decode(rawValue, validate=True)
            except ValueError as e:
                raise ValueError(f"Value data is not valid base64: {e}") from e
            return Value(rawBytes)
        case ValueType.PATH:
            if isinstance(rawValue, str):
                return Value(Path([rawValue]))
            if not isinstance(rawValue, list):
                raise ValueError(f"Value type declares path, but value is {type(rawValue)}")
            path = _createPathFromList(rawValue)
            return Value(path)
        case ValueType.LIST:
            if not isinstance(rawValue, list):
                raise ValueError(f"Value type declares list, but value is {type(rawValue)}")
            if len(rawValue) % 2 != 0:
                raise ValueError("List value must contain type/value pairs")
            items: list[Value] = []
            for i in range(0, len(rawValue), 2):
                t, v = rawValue[i], rawValue[i + 1]
                items.append(_decodeValue({JsonEncoding.VALUE_TYPE_KEY: t, "value": v}))
            return Value(items)
        case ValueType.MAP:
            if not isinstance(rawValue, list):
                raise ValueError(f"Value type declares map / dict, but value is {type(rawValue)}")
            if len(rawValue) % 3 != 0:
                raise ValueError("Map value must contain key/type/value triples")
            entries: dict[str, Value] = dict()
            for i in range(0, len(rawValue), 3):
                k, t, v = rawValue[i], rawValue[i + 1], rawValue[i + 2]
                if not isinstance(k, str):
                    raise ValueError(f"Map keys must be strings, not {type(k)}")
                entries[k] = _decodeValue({JsonEncoding.VALUE_TYPE_KEY: t, "value": v})
            return Value(entries)
        case ValueType.NONE:
            if rawValue is not None:
                raise ValueError("Value type declares null, but value is not null")
            return Value(None)
        case _:
            raise ValueError(f"Unknown value type: {rawType}")

def _createPathFromList(rawValue: list[Any]) -> Path:
    for component in rawValue:
        if not isinstance(component, str):
            raise ValueError("Paths must be a list of strings")
    return Path(rawValue)
