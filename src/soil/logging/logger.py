from abc import ABC, abstractmethod

from .level import LogLevel

from ..requests import Request


class Logger(ABC):
    """
    A type that receives log messages with different priority levels.
    """

    @abstractmethod
    def setLevel(self, level: LogLevel | None) -> Request:
        """
        Set the filtering level for this logger.

        If `nil` is provided as the level, then the logger may use the default level,
        or use the level of a parent node.

        Parameters
        ----------
        level : LogLevel
            The log level to use
        """
        pass

    @abstractmethod
    async def getLevel(self) -> LogLevel:
        """
        Get the current log level of this logger
        """
        pass

    @abstractmethod
    def child(self, component: str) -> Logger:
        """
        Creates a child logger under this logger.
        The child may inherit the parent's log level threshold.

        Parameters
        ----------
        component: str
            The subcomponent name

        Returns
        -------
        Logger
            A new ``Logger`` instance representing the child
        """
        pass

    def childWithLevel(self, component: str, level: LogLevel) -> Logger:
        """
        Creates a child logger under this logger.

        Parameters
        ----------
        component: str
            The subcomponent name
        level: LogLevel
            The log level to set for the child

        Returns
        -------
        Logger
            A new ``Logger`` instance representing the child
        """
        child = self.child(component)
        child.setLevel(level)
        return child

    @abstractmethod
    def log(self, level: LogLevel, message: str, *args: object) -> Request:
        """
        Log a message at the given level.

        Messages below the logger's level are ignored

        Parameters
        ----------
        level : LogLevel
            The level of the message
        message : str
            The message to log
        args : object
            Any number of additional format arguments for the message

        Returns
        -------
        Request
            A request to wait until the operation is completed
        """
        pass

    def trace(self, message: str, *args: object) -> Request:
        """
        Log a trace message.

        The message is ignored if the log level is higher than `trace`.

        Parameters
        ----------
        message: (str)
            The message to log
        args : object
            Any number of additional format arguments for the message

        Returns
        ------
        Request
            A request to wait for completion
        """
        return self.log(LogLevel.TRACE, message, *args)

    def debug(self, message: str, *args: object) -> Request:
        """
        Log a debug message.

        The message is ignored if the log level is higher than `debug`.

        Parameters
        ----------
        message: (str)
            The message to log
        args : object
            Any number of additional format arguments for the message

        Returns
        ------
        Request
            A request to wait for completion
        """
        return self.log(LogLevel.DEBUG, message, *args)

    def info(self, message: str, *args: object) -> Request:
        """
        Log an info message.

        The message is ignored if the log level is higher than `info`.

        Parameters
        ----------
        message: (str)
            The message to log
        args : object
            Any number of additional format arguments for the message

        Returns
        ------
        Request
            A request to wait for completion
        """
        return self.log(LogLevel.INFO, message, *args)

    def warning(self, message: str, *args: object) -> Request:
        """
        Log a warning message.

        The message is ignored if the log level is higher than `warning`.

        Parameters
        ----------
        message: (str)
            The message to log
        args : object
            Any number of additional format arguments for the message

        Returns
        ------
        Request
            A request to wait for completion
        """
        return self.log(LogLevel.WARNING, message, *args)

    def error(self, message: str, *args: object) -> Request:
        """
        Log an error message.

        The message is ignored if the log level is higher than `error`.

        Parameters
        ----------
        message: (str)
            The message to log
        args : object
            Any number of additional format arguments for the message

        Returns
        ------
        Request
            A request to wait for completion
        """
        return self.log(LogLevel.ERROR, message, *args)
