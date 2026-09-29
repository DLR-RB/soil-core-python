from enum import StrEnum


class ValueType(StrEnum):

    NONE = "null"
    """ The absence of a value, represented as 'None' """

    DATA = "data"
    """ Unspecified binary data, represented as 'bytes' """

    INTEGER = "integer"
    """ A natural number, represented as  'int' """

    DOUBLE = "double"
    """ A decimal value, represented as 'float' """

    STRING = "string"
    """ A textual value, represented as 'str' """

    PATH = "path"
    """ A path value, represented as 'Path' """

    LIST = "list"
    """ A list of values """

    MAP = "map"
    """ A map of values keyed by strings """

