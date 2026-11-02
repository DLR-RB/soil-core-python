from typing import Any, override

from ...data.type import ValueType
from ...encoding.json.generic import JsonKey
from ...messaging.message_type import MessageType

from .generic import GenericJsonEncoding


class CompactJsonEncoding(GenericJsonEncoding):
    """
    JSON wire format for soil messages.
    """

    @override
    def _fieldName(self, key: JsonKey) -> str:
        match key:
            case JsonKey.MESSAGE_TYPE: return "m"
            case JsonKey.VALUE_TYPE: return "h" # for type "hint", 't' is used for time
            case JsonKey.PATH: return "p"
            case JsonKey.COUNT: return "c"
            case JsonKey.DEPTH: return "d"
            case JsonKey.TIME: return "t"
            case JsonKey.END: return "e"
            case JsonKey.ID: return "i"
            case JsonKey.SAMPLES: return "s"
            case JsonKey.CHILDREN: return "n" # for 'nodes', 'c' is used for count
            case JsonKey.VALUE: return "v"

    @override
    def _encodeMessageType(self, type: MessageType) -> int | str:
        match type:
            case MessageType.DATA: return 0
            case MessageType.REQUEST: return 1
            case MessageType.DELETION: return 2
            case MessageType.SUBSCRIPTION_INCLUSION: return 3
            case MessageType.SUBSCRIPTION_EXCLUSION: return 4
            case MessageType.SUBSCRIPTION_DELETION: return 5

    @override
    def _decodeMessageType(self, raw: Any) -> MessageType:
        if not isinstance(raw, int):
            raise ValueError(f"Invalid message type '{raw}'")
        match raw:
            case 0: return MessageType.DATA
            case 1: return MessageType.REQUEST
            case 2: return MessageType.DELETION
            case 3: return MessageType.SUBSCRIPTION_INCLUSION
            case 4: return MessageType.SUBSCRIPTION_EXCLUSION
            case 5: return MessageType.SUBSCRIPTION_DELETION
            case _: raise ValueError(f"Unknown message type '{raw}'")

    @override
    def _encodeValueType(self, type: ValueType) -> int | str:
        match type:
            case ValueType.NONE: return 0
            case ValueType.INTEGER: return 1
            case ValueType.DOUBLE: return 2
            case ValueType.STRING: return 3
            case ValueType.DATA: return 4
            case ValueType.PATH: return 5
            case ValueType.LIST: return 6
            case ValueType.MAP: return 7

    def _decodeValueType(self, raw: Any) -> ValueType:
        if not isinstance(raw, int):
            raise ValueError(f"Invalid value type '{raw}'")
        match raw:
            case 0: return ValueType.NONE
            case 1: return ValueType.INTEGER
            case 2: return ValueType.DOUBLE
            case 3: return ValueType.STRING
            case 4: return ValueType.DATA
            case 5: return ValueType.PATH
            case 6: return ValueType.LIST
            case 7: return ValueType.MAP
            case _: raise ValueError(f"Unknown value type '{raw}'")
