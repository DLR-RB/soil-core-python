from asyncio import Lock
from typing import override

from ..components import Receiver
from ..data import Path, Timestamp, Value
from ..requests import AsyncRequest, CompletedRequest, Request
from .level import LogLevel
from .logger import Logger


class SimpleLogger(Logger):
    """
    A simple implementation of `Logger` that uses non-persistent log levels,
    and only requires a receiver.

    This class is not an actor, because it's not possible to implement `log()`
    with actor isolation. It needs to access the internal level safely, but
    formatted arguments may not be safely shared across concurrent contexts.

    Instead, we use a lock to access the property safely.
    """

    defaultLevel = LogLevel.WARNING
    """ The default level for logging when no explicit level is set. """

    def __init__(
        self,
        path: Path,
        receiver: Receiver,
        level: LogLevel | None = None
    ):
        """
        Create a new logger.

        :param path: The path to use for the log messages
        :param receiver: The receiver that handles the log messages
        :param level: The log level to use for filtering messages
        """
        # The path with which the log messages are published.
        self._path = path

        # The receiver to which the log messages are forwarded to
        self._receiver = receiver

        """
        The stored log level for this logger.

        We need to protect this property because this class is not an actor.
        We use a lock to access the property safely.
        """
        self.__level = level if level is not None else SimpleLogger.defaultLevel

        # The lock to safely access the stored log level
        self._lock = Lock()

    """
    Set the filtering level for this logger.

    :param level: The new level (None will set the default level)
    :returns: A request to wait for completion
    """
    @override
    def setLevel(self, level: LogLevel | None) -> Request:
        async def operation():
            async with self._lock:
                self.__level = level if level is not None else SimpleLogger.defaultLevel

        return AsyncRequest(operation())

    """
    Get the current log level of this logger.
    """
    @override
    async def getLevel(self) -> LogLevel:
        async with self._lock:
            return self.__level

    """
    Log a message at the given level.

    Messages below the logger's level are ignored.

    :param level: The level of the message
    :param message: The message to log
    :returns: A request to wait until the operation is completed
    """
    @override
    def log(self, level: LogLevel, message: str, *args: object) -> Request:
        if level < self.__level:
            return CompletedRequest()

        return self._write(level, message)

    """
    Log a formatted string at the given level.

    Messages below the logger's level are ignored.
    Logs a string initialized by using the given format string as a template
    into which the remaining argument values are substituted according to the
    user's default locale.

    :param level: The log level of the message
    :param format: The log message
    :param arguments: The arguments for the format string
    """
    def logFormat(
        self,
        level: LogLevel,
        format: str,
        *arguments: object,
    ) -> Request:
        if level < self.__level:
            return CompletedRequest()

        message = format % tuple(arguments)
        return self._write(level, message)

    # MARK: Child loggers

    """
    Creates a child logger under this logger.
    The child inherits the parent's log level threshold.

    :param component: The subcomponent name
    :returns: A new `Logger` instance representing the child
    """
    def childLogger(self, component: str) -> 'Logger':
        """
        Create a child logger under this logger.

        The child inherits the parent's log level threshold.

        :param component: The subcomponent name
        :returns: A new `Logger` instance representing the child
        """
        return SimpleLogger(
            path = self._path + [component],
            receiver = self._receiver,
            level = self.__level,
        )
    # MARK: Helper

    def _write(self, level: LogLevel, message: str) -> Request:
        return self._receiver.acceptValue(
            value = Value(message),
            path = self._path + [str(level)],
            timestamp = Timestamp.current(),
        )
