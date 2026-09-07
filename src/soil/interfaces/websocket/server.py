from collections.abc import Awaitable, Callable
import websockets
from websockets import ServerConnection

from ...logging import Logger, NoLogger, PrintLogger, LogLevel

from .connection import WebSocketConnection


class WebSocketServer:
    """
    A class to provide a web socket server.

    This class expects frame-based communication using bytes
    """

    def __init__(self, *,
        host: str = 'localhost',
        port: int,
        path: str | None = None,
        logger: Logger | None = None
    ) -> None:
        self.host = host
        self.port = port
        if path is not None:
            self.path = "/" + path.lstrip("/").rstrip("/") # Ensure a single slash leading the path
        else:
            self.path = None
        self.log = logger or NoLogger()
        self._server = None

    def onConnection(
        self,
        consumer: Callable[[WebSocketConnection], Awaitable[None]] | None,
    ) -> None:
        """
        Register a consumer of incoming connections.

        :param consumer: The new consumer of incoming connections.
        """
        self._connectionListener = consumer

    @property
    def isRunning(self) -> bool:
        """
        Indicate if the server is running.

        :return: True if the server is running.
        """
        return self._server is not None and self._server.is_serving()

    async def serve(self) -> bool:
        """
        Start the websocket server.
        """
        if self.isRunning:
            self.log.info("Already started")
            return True
        try:
            self._server = await websockets.serve(self._handler, self.host, self.port)
            self.log.info(f"Listening on ws://{self._connectionUri}")
            return True
        except Exception as e:
            self.log.error(f"Failed to start on ws://{self._connectionUri}: {e}")
            return False
        #

    @property
    def _connectionUri(self) -> str:
        base = f"{self.host}:{self.port}"
        if self.path is None:
            return base
        return base + self.path # Path contains leading slash

    async def _handler(self, websocket: ServerConnection):
        """
        Handles each incoming connection.
        """
        if self.path is not None:
            if websocket.request is None:
                self.log.warning("Ignoring connection without a request")
                return
            if websocket.request.path != self.path: # Path contains leading slash
                self.log.warning(f"Ingnoring connection on invalid path: {websocket.request.path}")
                await websocket.close(code=1008, reason="Invalid path")
                return
            #
        self.log.info(f"New client connected: {websocket.remote_address} ({websocket.state})")
        if self._connectionListener is None:
            self.log.warning("No handler registered for connected client")
            return
        connection = WebSocketConnection(websocket, logger=PrintLogger(level = LogLevel.INFO))
        await self._connectionListener(connection)
        await websocket.wait_closed()

    async def close(self) -> None:
        if self._server is None:
            return
        self._server.close()
        self._server = None
