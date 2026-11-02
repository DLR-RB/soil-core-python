from abc import abstractmethod
from enum import Enum
from typing import Any, override
from base64 import b64decode, b64encode
from json import dumps, loads

from ...data import Path, Sample, SampleTree, Timestamp, Value, ValueType
from ...messaging import MessageType, MessageEncoding, Message


class JsonKey(Enum):
    """ A key used in JSON encoding """

    MESSAGE_TYPE = 0
    VALUE_TYPE = 1
    PATH = 2
    COUNT = 3
    DEPTH = 4
    TIME = 5
    END = 6
    ID = 7
    SAMPLES = 8
    CHILDREN = 9
    VALUE = 10


class GenericJsonEncoding(MessageEncoding):
    """ A generic JSON encoder that can be subclassed to provide customization of keys and encoding logic """

    @abstractmethod
    def _fieldName(self, key: JsonKey) -> str:
        ...

    @abstractmethod
    def _encodeMessageType(self, type: MessageType) -> int | str:
        ...

    @abstractmethod
    def _decodeMessageType(self, raw: Any) -> MessageType:
        ...

    @abstractmethod
    def _encodeValueType(self, type: ValueType) -> int | str:
        ...

    @abstractmethod
    def _decodeValueType(self, raw: Any) -> ValueType:
        ...

    # MARK: MessageEncoding

    @override
    def encode(self, message: Message) -> bytes:
        converted = self._encodeMessage(message)
        return dumps(converted).encode('utf-8')

    @override
    def decode(self, data: bytes) -> Message:
        raw = loads(data)
        return self._decodeMessage(raw)

    # MARK: Encoding

    def _encodeMessage(self, message: Message) -> dict[str, Any]:
        result:  dict[str, Any] = dict()
        # Only encode message type if not a data message
        if message.type != MessageType.DATA:
            result[self._fieldName(JsonKey.MESSAGE_TYPE)] = self._encodeMessageType(message.type)
        # If the path is absent, then it defaults to an empty path
        if not message.path.isEmpty:
            # Single-component paths are encoded as a plain string
            pathKey = self._fieldName(JsonKey.PATH)
            if len(message.path) == 1:
                result[pathKey] = message.path[0]
            else:
                result[pathKey] = message.path

        # There is a possibly invalid message where the `time` is set in addition to data being present
        # We ensure that the timestamp is not written into the message if any samples are provided
        # so that decoding does not fail
        self._encodeTree(message.data, result, message.time is None)

        if message.count is not None:
            result[self._fieldName(JsonKey.COUNT)] = message.count
        if message.depth is not None:
            result[self._fieldName(JsonKey.DEPTH)] = message.depth
        self._encodeTime(result, message.time)
        self._encodeTime(result, message.end, JsonKey.END)
        if message.id is not None:
            result[self._fieldName(JsonKey.ID)] = message.id
        return result

    def _encodeTime(self, container: dict[str, Any], time: Timestamp | None, key: JsonKey = JsonKey.TIME) -> None:
        if time is None:
            return
        container[self._fieldName(key)] = time.timeIntervalSince1970

    def _encodeTree(self, tree: SampleTree, container: dict[str, Any], canUseRoot: bool) -> None:
        samples = tree.samples
        if len(samples) == 1 and canUseRoot:
            # Encode a single sample at the top-level of the container,
            # but only if the 'time' field is not already used
            self._encodeSample(samples[0], container)
        elif len(samples) >= 1:
            container[self._fieldName(JsonKey.SAMPLES)] = [self._encodeSample(s, dict()) for s in samples]

        children = tree.children
        if len(children) == 0:
            return
        childList: dict[str, Any] = dict()
        for name, child in children.items():
            childContainer: dict[str, Any] = dict()
            self._encodeTree(child, childContainer, canUseRoot=True)
            childList[name] = childContainer
        container[self._fieldName(JsonKey.CHILDREN)] = childList

    def _encodeSample(self, sample: Sample, container: dict[str, Any]) -> dict[str, Any]:
        self._encodeValueInContainer(sample.value, container)
        self._encodeTime(container, sample.timestamp)
        return container

    def _encodeValueInContainer(self, value: Value, container: dict[str, Any]) -> None:
        valueType = value.type
        match valueType:
            case ValueType.INTEGER | ValueType.DATA | ValueType.LIST | ValueType.MAP:
                container[self._fieldName(JsonKey.VALUE_TYPE)] = self._encodeValueType(valueType)
            case ValueType.STRING | ValueType.DOUBLE | ValueType.NONE | ValueType.PATH:
                pass
        container[self._fieldName(JsonKey.VALUE)] = self._encodeValue(value)

    def _encodeValue(self, value: Value) -> Any:
        inner = value.value
        if isinstance(inner, bytes):
            return b64encode(inner).decode('ascii')
        elif isinstance(inner, Path):
            # Note: Path must be checked before list, because it is also a list
            return inner
        elif isinstance(inner, list):
            # Flatten nested values to [type, value, type, value, ...]
            items: list[Any] = []
            for element in inner:
                items.append(self._encodeValueType(element.type))
                items.append(self._encodeValue(element))
            return items
        elif isinstance(inner, dict):
            # Flatten nested values to [key, type, value, ...]
            items = []
            for key, element in inner.items():
                sub: dict[str, Any] = dict()
                self._encodeValueInContainer(element, sub)
                items.append(key)
                items.append(self._encodeValueType(element.type))
                items.append(self._encodeValue(element))
            return items
        else:
            return inner

    # MARK: Decoding

    def _decodeMessage(self, raw: Any) -> Message:
        if not isinstance(raw, dict):
            raise ValueError("Top-level JSON is not a dict")

        container: dict[str, Any] = raw # pyright: ignore[reportUnknownVariableType]

        type_msg = self._decodeMessageTypeFromContainer(container)
        path = self._decodePath(container)

        count = self._decodeInt(container, JsonKey.COUNT)
        depth = self._decodeInt(container, JsonKey.DEPTH)
        id = self._decodeInt(container, JsonKey.ID)

        # Note: If a value is encoded at the top level,
        # then the timestamp refers to it, and is ignored here
        time = None
        if not self._fieldName(JsonKey.VALUE) in container:
            time = self._decodeTime(container)

        end = self._decodeTime(container, JsonKey.END)

        # Data decoding consumes the value/type from the root (if present)
        data = self._decodeTree(container)

        return Message(type_msg, path, data, count, depth, time, end, id)

    def _decodeMessageTypeFromContainer(self, container: dict[str, Any]) -> MessageType:
        rawType = container.get(self._fieldName(JsonKey.MESSAGE_TYPE))
        if rawType is None:
            return MessageType.DATA
        return self._decodeMessageType(rawType)

    def _decodePath(self, container: dict[str, Any]) -> Path:
        rawPath = container.get(self._fieldName(JsonKey.PATH))
        if rawPath is None:
            return Path()
        # Note: Single-component paths can be encoded as plain strings
        if isinstance(rawPath, str):
            return Path([rawPath])
        if not isinstance(rawPath, list):
            raise ValueError("Message path must be a list of strings")
        return _createPathFromList(rawPath) # pyright: ignore[reportUnknownArgumentType]

    def _decodeInt(self, container: dict[str, Any], key: JsonKey) -> int | None:
        field = self._fieldName(key)
        raw = container.get(field)
        if raw is None:
            return None
        if isinstance(raw, bool):
            raise ValueError(f"Field '{field}' ({raw}) must be an integer, not bool")
        if not isinstance(raw, int):
            raise ValueError(f"Field '{field}' ({raw}) must be an integer, not {type(raw)}")
        return raw

    def _decodeTime(self, container: dict[str, Any], key: JsonKey = JsonKey.TIME) -> Timestamp | None:
        raw = container.get(self._fieldName(key))
        if raw is None:
            return None
        # Check boolean, since it is a subclass of int
        if isinstance(raw, float):
            return Timestamp.fromTimeIntervalSince1970(raw)
        if isinstance(raw, int):
            return Timestamp.fromTimeIntervalSince1970(float(raw))
        raise ValueError(f"Field 'time' ({raw}) must be a number, not {type(raw)}")

    def _decodeTree(self, container: dict[str, Any]) -> SampleTree:
        samples = self._decodeSamples(container)

        if self._fieldName(JsonKey.VALUE) in container:
            samples.append(self._decodeSample(container))

        samples.sort()
        children = self._decodeChildren(container)
        return SampleTree(samples, children)

    def _decodeChildren(self, container: dict[str, Any]) -> dict[str, SampleTree]:
        field = self._fieldName(JsonKey.CHILDREN)
        raw = container.get(field)
        if raw is None:
            return dict()
        if not isinstance(raw, dict):
            raise ValueError(f"Field '{field}' must be a dictionary, not {type(raw)}")

        children: dict[str, SampleTree] = dict()
        for name, child in raw.items(): # pyright: ignore[reportUnknownVariableType]
            if not isinstance(name, str):
                raise ValueError(f"Field '{field}' must have string keys, not {type(name)}") # pyright: ignore[reportUnknownArgumentType]
            if not isinstance(child, dict):
                raise ValueError(f"Field '{field}' must have dictionary values, not {type(child)}")  # pyright: ignore[reportUnknownArgumentType]
            children[name] = self._decodeTree(child) # pyright: ignore[reportUnknownArgumentType]
        return children

    def _decodeSamples(self, container: dict[str, Any]) -> list[Sample]:
        field = self._fieldName(JsonKey.SAMPLES)
        raw = container.get(field)
        if raw is None:
            return list()
        if not isinstance(raw, list):
            raise ValueError(f"Field '{field}' must be a list, not {type(raw)}")
        return [self._decodeSampleFromListElement(e) for e in raw] # pyright: ignore[reportUnknownVariableType]

    def _decodeSampleFromListElement(self, element: Any) -> Sample:
        if not isinstance(element, dict):
            raise ValueError(f'Sample must be represented as a dictionary, not {type(element)}')
        return self._decodeSample(element) # pyright: ignore[reportUnknownArgumentType]

    def _decodeSample(self, container: dict[str, Any]) -> Sample:
        value = self._decodeValue(container)
        timestamp = self._decodeTime(container)
        return Sample(value, timestamp)

    def _decodeValue(self, container: dict[str, Any]) -> Value:
        rawType = container.get(self._fieldName(JsonKey.VALUE_TYPE))
        valueField = self._fieldName(JsonKey.VALUE)
        rawValue = container.get(valueField)
        if rawType is not None:
            return self._decodeValueWithType(rawValue, rawType)
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
        raise ValueError(f"Field '{valueField}' has unknown type {type(rawValue)}")

    def _decodeValueWithType(self, rawValue: Any, rawType: Any) -> Value:
        valueType = self._decodeValueType(rawType)
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
                path = _createPathFromList(rawValue) # pyright: ignore[reportUnknownArgumentType]
                return Value(path)
            case ValueType.LIST:
                # Lists are encoded as (type, value, type, value, ...)
                if not isinstance(rawValue, list):
                    raise ValueError(f"Value type declares list, but value is {type(rawValue)}")
                if len(rawValue) % 2 != 0: # pyright: ignore[reportUnknownArgumentType]
                    raise ValueError("List value must contain type/value pairs")
                items: list[Value] = []
                for i in range(0, len(rawValue), 2): # pyright: ignore[reportUnknownArgumentType]
                    items.append(self._decodeValueWithType(rawValue[i + 1], rawValue[i]))
                return Value(items)
            case ValueType.MAP:
                if not isinstance(rawValue, list):
                    raise ValueError(f"Value type declares map / dict, but value is {type(rawValue)}")
                if len(rawValue) % 3 != 0: # pyright: ignore[reportUnknownArgumentType]
                    raise ValueError("Map value must contain key/type/value triples")
                entries: dict[str, Value] = dict()
                for i in range(0, len(rawValue), 3): # pyright: ignore[reportUnknownArgumentType]
                    k, t, v = rawValue[i], rawValue[i + 1], rawValue[i + 2] # pyright: ignore[reportUnknownVariableType]
                    if not isinstance(k, str):
                        raise ValueError(f"Map keys must be strings, not {type(k)}") # pyright: ignore[reportUnknownArgumentType]
                    entries[k] = self._decodeValueWithType(v, t)
                return Value(entries)
            case ValueType.NONE:
                if rawValue is not None:
                    raise ValueError(f"Value type declares null, but value is: {rawValue}")
                return Value(None)
        #

def _createPathFromList(rawValue: list[Any]) -> Path:
    for component in rawValue:
        if not isinstance(component, str):
            raise ValueError("Paths must be a list of strings")
    return Path(rawValue)
