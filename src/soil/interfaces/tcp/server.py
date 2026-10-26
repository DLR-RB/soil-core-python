import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress

from ...logging import Logger, OptionalLogger
from ...utils import ActorClosedError
from .connection import TcpSocketConnection


class TcpSocketServer:
    """
    TCP server exposing each connection as a StreamConnection
    """

    def __init__(self, *, host: str = "0.0.0.0", port: int, logger: Logger | None = None) -> None:
        """
        Create a TCP server for connection.

        :param port: The local port to use for the server.
        :param logger: The logger to use for internal messages and issues.
        """
        self._requestedHost = host
        self._requestedPort = port
        self._server: asyncio.base_events.Server | None = None
        self._running = False

        #: The consumer of new incoming connections
        self._connectionListener: Callable[[TcpSocketConnection], Awaitable[None]] | None = None

        #: The logger to use for internal messages
        self._log = OptionalLogger()
        self._log.setLogger(logger)

        self._serverTask: asyncio.Task[None] | None = None
        self._started = asyncio.Event()

        self._connections: list[TcpSocketConnection] = list()

    @property
    def numberOfConnections(self) -> int:
        return len(self._connections)

    async def numberOfActiveConnections(self) -> int:
        await self._clearClosedConnections()
        return self.numberOfConnections

    def getLogger(self) -> Logger | None:
        """
        Get the current logger.

        :return: The currently used logger.
        """
        return self._log.getLogger()

    def setLogger(self, logger: Logger | None) -> None:
        """
        Set the logger for internal messages.

        :param logger: The new logger to use.
        """
        self._log.setLogger(logger)

    def getLocalPort(self) -> int:
        """
        Returns the actual port the server is listening on.

        :return: The local port.
        """
        if self._server is None:
            raise RuntimeError("Server not started yet")

        socket = self._server.sockets[0]
        return socket.getsockname()[1]

    async def waitForPort(self) -> int:
        """
        Wait for the local port until the socket is bound.

        :return: The local port, or -1 if the server did not start.
        """
        tries = 10

        while tries > 0:
            if self._server is not None:
                return self.getLocalPort()

            await asyncio.sleep(0.05)
            tries -= 1

        return -1

    def isRunning(self) -> bool:
        """
        Indicate if the server is running.

        :return: True if the server is running.
        """
        return self._running

    def onConnection(
        self,
        consumer: Callable[[TcpSocketConnection], Awaitable[None]] | None,
    ) -> None:
        """
        Register a consumer of incoming connections.

        :param consumer: The new consumer of incoming connections.
        """
        self._connectionListener = consumer

    async def start(self) -> bool:
        """
        Start the server.

        :return: True if the server was started.
        """
        task = await self._startTask()
        if task is None:
            return False
        self._serverTask = task
        return True

    async def startAndWaitForConnections(self) -> None:
        """
        Start the server and continuously handle new connections via the
        provided handler.

        The handler will be called with each new connection.
        """
        task = await self._startTask()
        if task is not None:
            await task

    async def _startTask(self) -> asyncio.Task[None] | None:
        if self.isRunning():
            self._log.info("Server is already running")
            return None

        self._log.info(f"Starting server on port {self._requestedPort}")

        try:
            self._server = await asyncio.start_server(
                self._handleConnection,
                host=self._requestedHost,
                port=self._requestedPort,
            )
        except Exception as exc:
            self._log.error(
                f"Failed to start on port {self._requestedPort}: {exc}"
            )
            return None

        self._running = True
        self._started.set()

        self._log.info("Waiting for connections")

        # Equivalent to starting a virtual thread.
        return asyncio.create_task(self._serve())

    async def _serve(self) -> None:
        """
        Continuously handle new connections via the provided handler.

        The handler will be called with each new connection.
        The handler must not block, or no additional connections will be
        accepted until the handler finishes.
        """
        if self._server is None:
            return

        try:
            async with self._server:
                await self._server.serve_forever()

        except asyncio.CancelledError:
            pass

        except Exception as exc:
            if self.isRunning():
                self._log.error(f"Failed while serving: {exc}")

        finally:
            self._running = False
            self._server = None

    async def _handleConnection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        peer = writer.get_extra_info("peername")
        self._log.info(f"New connection from {peer}")

        connection = TcpSocketConnection(
            reader,
            writer,
            logger=self._log.getLogger(),
        )

        # Track the connection to close it when the server shuts down
        await self._clearClosedConnections()
        self._connections.append(connection)

        if self._connectionListener is not None:
            await self._connectionListener(connection)
        else:
            self._log.warning("No handler registered for new connection")

    async def stop(self) -> bool:
        """
        Gracefully stops the server and closes all client connections.

        :return: True if the server was stopped or has been stopped.
        """
        if not self.isRunning():
            self._log.warning("Server is already stopped")
            return True

        self._running = False

        if self._server is not None:
            try:
                self._log.info("Closing socket")
                self._server.close()
                await self._cancelConnections()
                # Note: self._server may be set null by another task
                if self._server is not None: # pyright: ignore[reportUnnecessaryComparison]
                    await self._server.wait_closed()
            except Exception as e:
                self._log.warning(f"Failed to close server socket: {e}")
                print(f"Failed to close server: {e}")
                return False

            self._log.info("Socket closed")

        if self._serverTask is not None:
            self._serverTask.cancel()
            with suppress(asyncio.CancelledError):
                await self._serverTask

        self._server = None

        self._log.info("Server stopped")
        return True

    async def _clearClosedConnections(self):
        remaining: list[TcpSocketConnection] = list()
        for connection in self._connections:
            try:
                is_open = await connection.isOpen()
            except ActorClosedError:
                is_open = False
            if is_open:
                remaining.append(connection)
            else:
                await connection.shutdown()
        self._connections = remaining

    async def _cancelConnections(self):
        for connection in self._connections:
            try:
                await connection.close()
            except ActorClosedError:
                pass
            await connection.shutdown()
        self._connections = []
