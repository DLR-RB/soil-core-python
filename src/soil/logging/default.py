from typing import override

from ..components import Receiver
from ..data import Path, Timestamp, Value
from ..nodes.receiver.defaults import DefaultStringReceiverNode
from ..requests import AsyncRequest, CompletedRequest, Request
from .level import LogLevel
from .logger import Logger


class DefaultLogger(DefaultStringReceiverNode, Logger):
    """
    A simple logger that uses a non-persistent log level
    to work directly with receivers.
    """

    def __init__(
        self,
        path: Path,
        receiver: Receiver,
        level: LogLevel,
    ) -> None:
        """
        Constructor for root or child loggers.

        :param path: The path of the logging node in the tree.
        :param receiver: The backend consumer; never None.
        :param level: The initial log level threshold for this node.
        """
        super().__init__(
            receiver,
            path,
        )

        #: The log level of this logger
        self._level: LogLevel = level

    @override
    def setLevel(self, level: LogLevel) -> Request:
        """
        Updates the log level threshold for this logger.

        :param level: The new log level.
        """
        self._level = level
        return CompletedRequest()

    @override
    async def getLevel(self) -> LogLevel:
        """
        Returns the current log level threshold.

        :return: The current log level.
        """
        return self._level

    def isDisabled(self, level: LogLevel) -> bool:
        """
        Check if a log level is disabled.

        :param level: The level to check.
        :return: True if messages with the given log level are ignored.
        """
        return level < self._level

    @override
    def log(
        self,
        level: LogLevel,
        message: str,
        *args: object,
    ) -> Request:
        """
        Log a message at the given level.

        Messages below the logger's level are ignored.

        :param msgLevel: The log level of the message.
        :param message: The log message.
        """
        if self.isDisabled(level):
            # Early exit for messages below the threshold
            return CompletedRequest()

        if args:
            message = message % args

        return AsyncRequest(self._logUnconditionally(level, message))

    # MARK: Internal functions

    async def _logUnconditionally(
        self,
        msgLevel: LogLevel,
        message: str,
    ) -> None:
        """
        Send a message to the backend receiver.
        """

        await self.receiver().acceptValue(
            value = Value(message),
            path = self.path().appending(msgLevel.stringValue),
            timestamp = Timestamp.current(),
        )

    # MARK: Child loggers

    @override
    def childLogger(self, component: str, level: LogLevel | None = None) -> Logger:
        """
        Creates a child logger under this logger hierarchy.

        The child inherits the parent's log level threshold unless a new
        level is supplied.

        :param component: The subcomponent name.
        :param level: The log level to set for the child.
        :return: A new Logger instance representing the child.
        """
        return DefaultLogger(
            self.path().appending(component),
            self.receiver(),
            self._level if level is None else level,
        )
