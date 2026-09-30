from asyncio import open_connection

from ...logging import Logger
from .connection import TcpSocketConnection


class TcpSocketClient:
    """
    TCP client exposing a connected StreamConnection
    """

    def __init__(self, host: str, port: int) -> None:
        """
        Create a TCP client to connect.

        :param host: The host of the socket to connect to.
        :param port: The port of the socket.
        """
        self._host = host
        self._port = port

    async def connect(self, logger: Logger | None = None) -> TcpSocketConnection:
        """
        Connect to server and get the connection.

        :param log: The logger to use for the connection.
        :return: The stream connection for the socket.
        :raises OSError: If the connection fails.
        """
        reader, writer = await open_connection(self._host, self._port)
        return TcpSocketConnection(reader, writer, logger)
