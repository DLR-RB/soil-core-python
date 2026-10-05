from typing import override

from ..requests import CompletedRequest, Request
from .level import LogLevel
from .logger import Logger


class NoLogger(Logger):
    """
    A logger that ignores all log messages, regardless of level
    """

    def __init__(self) -> None:
        self._level = LogLevel.WARNING

    @override
    def setLevel(self, level: LogLevel | None) -> Request:
        self._level = level if level is not None else LogLevel.WARNING
        return CompletedRequest()

    @override
    async def getLevel(self) -> LogLevel:
        return self._level

    @override
    def childLogger(self, component: str, level: LogLevel | None = None) -> Logger:
        logger = NoLogger()
        logger.setLevel(level)
        return logger

    @override
    def log(self, level: LogLevel, message: str, *args: object) -> Request:
        return CompletedRequest()
