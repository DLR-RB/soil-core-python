from websockets import connect

from ...framing.receiver import FrameReceiver
from ...logging import Logger, NoLogger
from .connection import WebSocketConnection


class WebSocketClient:
    """
    A class to connect a web socket as a client.

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
        self.path = path
        self.log = logger or NoLogger()

    @property
    def connectionUri(self) -> str:
        uri = f"ws://{self.host}:{self.port}"
        if self.path is not None and self.path != "":
            uri = f"{uri}/{self.path}"
        return uri

    async def connect(self,
        receiver: FrameReceiver | None = None,
        logger: Logger | None = None
    ) -> WebSocketConnection:
        """
        Create a connection to the websocket server

        Raises:
            OSError, ConnectionRefusedError, TimeoutError, InvalidHandshake
        """
        uri = self.connectionUri
        self.log.debug(f"Connecting to {uri}")
        connection = await connect(uri, proxy=None) # local_addr=("0.0.0.0", 50000))
        self.log.info(f"Connected to {uri}")
        return WebSocketConnection(connection, receiver, logger)
