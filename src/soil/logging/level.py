from enum import IntEnum

class LogLevel(IntEnum):

    TRACE = 0

    DEBUG = 1

    INFO = 2

    WARNING = 3

    ERROR = 4

    @staticmethod
    def fromString(raw: str) -> LogLevel | None:
        """
        Create a log level from a raw string
        """
        match raw:
            case "trace":
                return LogLevel.TRACE
            case "debug":
                return LogLevel.DEBUG
            case "info":
                return LogLevel.INFO
            case "warning":
                return LogLevel.WARNING
            case "error":
                return LogLevel.ERROR
            case _:
                return None

    def __str__(self) -> str:
        match self:
            case LogLevel.TRACE:
                return "trace"
            case LogLevel.DEBUG:
                return "debug"
            case LogLevel.INFO:
                return "info"
            case LogLevel.WARNING:
                return "warning"
            case LogLevel.ERROR:
                return "error"