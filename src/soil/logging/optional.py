from typing import override

from ..requests import AsyncRequest, CompletedRequest, Request
from .level import LogLevel
from .logger import Logger


class OptionalLogger(Logger):
    """
    A convenience wrapper to better work with nullable loggers
    """

    def __init__(self, logger: Logger | None = None) -> None:
        """
        Wrap a logger.

        :param logger: The logger to wrap.
        """
        self._logger = logger

    def setLogger(self, logger: Logger | None) -> None:
        """
        Set the wrapped logger.

        :param logger: The logger to wrap.
        """
        self._logger = logger

    def getLogger(self) -> Logger | None:
        """
        Get the currently wrapped logger.

        :return: The current logger.
        """
        return self._logger

    @override
    def setLevel(self, level: LogLevel) -> Request:
        if self._logger is None:
            return CompletedRequest()

        return AsyncRequest(self._logger.setLevel(level))

    @override
    async def getLevel(self) -> LogLevel:
        if self._logger is None:
            return LogLevel.WARNING

        return await self._logger.getLevel()

    @override
    def log(
        self,
        level: LogLevel,
        message: str,
        *args: object,
    ) -> Request:
        if self._logger is None:
            return CompletedRequest()

        # The default implementation is not efficient,
        # because the format string is constructed even if the message is ignored
        return AsyncRequest(self._logger.log(level, message, *args))

    def childLogger(
        self,
        component: str,
        level: LogLevel | None = None,
    ) -> Logger:
        if self._logger is None:
            return OptionalLogger()

        if level is None:
            return self._logger.childLogger(component)

        return self._logger.childWithLevel(component, level)
