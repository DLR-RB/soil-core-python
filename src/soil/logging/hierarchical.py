from typing import Optional, override

from ..components import Storage
from ..data import Path, Timestamp, Value
from ..nodes import StorageNode
from ..requests import Request, AsyncRequest
from .logger import Logger
from .level import LogLevel


class HierarchicalLogger(Logger):
    """
    A logger implementation that uses the log level of parent nodes
    if no specific log level is set.
    This allows changing the log level for entire logging trees at once.

    Note:
        The `log(messageLevel, message)` function always creates the message,
        even if it is discarded due to the log level. This mirrors the Swift
        implementation, where formatting occurs before the level check.
    """

    defaultLevel: LogLevel = LogLevel.WARNING
    """ The default level for logging when no explicit level is set. """

    def __init__(self, node: StorageNode, parent: Optional[Logger] = None) -> None:
        self._parent = parent
        self._logNode = node
        self._levelNode = node.child(named="level")

    @classmethod
    def create(cls, storage: Storage, path: Path | None = None) -> 'HierarchicalLogger':
        """
        Create a logger for a storage at a path.

        Args:
            storage: The storage to use as the logging backend.
            path: The path to use for the logger.
        """
        if path is None:
            path = Path()

        return cls(
            node=StorageNode(storage=storage, path=path),
        )

    @override
    def setLevel(self, level: LogLevel | None) -> Request:
        """
        Set the filtering level for this logger.

        If `None` is provided as the level, then the logger uses
        the first available level of a parent node up to the root,
        or the default level.

        Args:
            level: The log level to use.

        Returns:
            A request to wait for the application of the level.
        """
        if level is not None:
            return self._levelNode.setString(level.stringValue)
        return self._levelNode.setNull()

    @override
    async def getLevel(self) -> LogLevel:
        """
        Get the current log level of this logger.

        If no explicit level is set for this logger,
        then the level of the parent is used.
        """
        raw = await self._levelNode.stringValue()

        if raw is not None:
            level = LogLevel.fromString(raw)
            if level is not None:
                return level

        if self._parent is None:
            return HierarchicalLogger.defaultLevel

        return await self._parent.getLevel()

    # MARK: Generic logging

    @override
    def log(self, level: LogLevel, message: str, *args: object) -> Request:
        """
        Log a message at the given level.

        Messages below the logger's level are ignored.

        Args:
            level: The level of the message.
            message: The message to log.

        Returns:
            A request to wait until the operation is completed.
        """

        async def operation() -> None:
            effectiveLevel = await self.getLevel()

            if level < effectiveLevel:
                return

            self._logNode.acceptValue(
                Value(message),
                path = Path.of(level.stringValue),
                timestamp = Timestamp.current(),
            )

        return AsyncRequest(operation())

    # MARK: Child loggers

    @override
    def child(self, component: str) -> Logger:
        """
        Creates a child logger under this logger.
        The child may inherit the parent's log level threshold.

        Args:
            component: The subcomponent name.

        Returns:
            A new ``Logger`` instance representing the child.
        """
        return HierarchicalLogger(
            parent=self,
            node=self._logNode.child(named=component),
        )
