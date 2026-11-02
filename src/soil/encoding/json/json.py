from typing import Any, override

from ...data.type import ValueType
from ...encoding.json.generic import JsonKey
from ...messaging.message_type import MessageType

from .generic import GenericJsonEncoding


class JsonEncoding(GenericJsonEncoding):
    """
    JSON wire format for soil messages.
    """

    @override
    def _fieldName(self, key: JsonKey) -> str:
        match key:
            case JsonKey.MESSAGE_TYPE: return "message"
            case JsonKey.VALUE_TYPE: return "type"
            case JsonKey.PATH: return "path"
            case JsonKey.COUNT: return "count"
            case JsonKey.DEPTH: return "depth"
            case JsonKey.TIME: return "time"
            case JsonKey.END: return "end"
            case JsonKey.ID: return "id"
            case JsonKey.SAMPLES: return "samples"
            case JsonKey.CHILDREN: return "children"
            case JsonKey.VALUE: return "value"

    @override
    def _encodeMessageType(self, type: MessageType) -> int | str:
        match type:
            case MessageType.DATA: return "data"
            case MessageType.REQUEST: return "read"
            case MessageType.DELETION: return "delete"
            case MessageType.SUBSCRIPTION_INCLUSION: return "include"
            case MessageType.SUBSCRIPTION_EXCLUSION: return "exclude"
            case MessageType.SUBSCRIPTION_DELETION: return "clear"

    @override
    def _decodeMessageType(self, raw: Any) -> MessageType:
        if not isinstance(raw, str):
            raise ValueError(f"Invalid message type '{raw}'")
        match raw:
            case "data": return MessageType.DATA
            case "read": return MessageType.REQUEST
            case "delete": return MessageType.DELETION
            case "include": return MessageType.SUBSCRIPTION_INCLUSION
            case "exclude": return MessageType.SUBSCRIPTION_EXCLUSION
            case "clear": return MessageType.SUBSCRIPTION_DELETION
            case _: raise ValueError(f"Unknown message type '{raw}'")

    @override
    def _encodeValueType(self, type: ValueType) -> int | str:
        match type:
            case ValueType.NONE: return "null"
            case ValueType.DATA: return "data"
            case ValueType.INTEGER: return "integer"
            case ValueType.DOUBLE: return "double"
            case ValueType.STRING: return "string"
            case ValueType.PATH: return "path"
            case ValueType.LIST: return "list"
            case ValueType.MAP: return "map"

    def _decodeValueType(self, raw: Any) -> ValueType:
        if not isinstance(raw, str):
            raise ValueError(f"Invalid value type '{raw}'")
        match raw:
            case "null": return ValueType.NONE
            case "data": return ValueType.DATA
            case "integer": return ValueType.INTEGER
            case "double": return ValueType.DOUBLE
            case "string": return ValueType.STRING
            case "path": return ValueType.PATH
            case "list": return ValueType.LIST
            case "map": return ValueType.MAP
            case _: raise ValueError(f"Unknown value type '{raw}'")
