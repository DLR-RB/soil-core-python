from typing import override

from ..data.path import Path
from ..requests import Request, CompletedRequest

from .level import LogLevel
from .logger import Logger


class PrintLogger(Logger):
    """
    A logger that prints log messages.
    """

    def __init__(self, path: Path = Path(), level: LogLevel | None = None) -> None:
        self._level: LogLevel = level or LogLevel.WARNING
        self.path: Path = path

    @override
    def setLevel(self, level: LogLevel | None) -> Request:
        self._level = level or LogLevel.WARNING
        return CompletedRequest()

    @override
    async def getLevel(self) -> LogLevel:
        return self._level

    @override
    def child(self, component: str, level: LogLevel | None = None) -> Logger:
        logger = PrintLogger(self.path.appending(component), level)
        logger.setLevel(level)
        return logger

    @override
    def log(self, level: LogLevel, message: str, *args: object) -> Request:
        if level >= self._level:
            msg = message.format(args)
            print(f"[{str(level).upper()}][{self.path}] {msg}")
        return CompletedRequest()
