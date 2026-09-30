from asyncio import sleep
from typing import override
from unittest import IsolatedAsyncioTestCase

from soil.components import Receiver
from soil.connection import RemoteTransmitter
from soil.data import ImmutableSampleTree, Path, SampleTree, Value
from soil.encoding.json import JsonEncoding
from soil.interfaces.websocket import (
    WebSocketClient,
    WebSocketConnection,
    WebSocketServer,
)
from soil.logging import LogLevel, PrintLogger
from soil.requests import CompletedRequest, Request


class TestReceiver(Receiver):

    def __init__(self) -> None:
        self.received: tuple[SampleTree, Path] | None = None

    @override
    def accept(self, tree: SampleTree, path: Path) -> Request:
        self.received = (tree, path)
        return CompletedRequest()


class WebsocketTests(IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.serverToClient: WebSocketConnection | None = None

    async def testClientServerTransmit(self) -> None:
        level=LogLevel.WARNING

        server = WebSocketServer(
            port = 0,
            path = "some",
            logger = PrintLogger(path=Path.of("server"), level=level)
        )

        async def acceptClient(connection: WebSocketConnection):
            self.serverToClient = connection
            connection.log = PrintLogger(path=Path.of("socket s->c"), level=level)

        server.onConnection(acceptClient)
        await server.serve()

        actual_port = server.port

        client = WebSocketClient(
            port = actual_port,
            path = "some",
            logger = PrintLogger(path=Path.of("client"), level=level)
        )
        clientToServer = await client.connect(logger = PrintLogger(path=Path.of("socket c->s"), level=level))
        await sleep(0.1)
        self.assertIsNotNone(self.serverToClient)
        if self.serverToClient is None: return

        self.assertTrue(await self.serverToClient.isOpen())
        self.assertTrue(await clientToServer.isOpen())

        toServer = await clientToServer.apply(JsonEncoding(), PrintLogger(level=level))
        toClient = await self.serverToClient.apply(JsonEncoding(), PrintLogger(level=level))

        receiver = TestReceiver()
        remoteClient = await RemoteTransmitter.create(toClient)
        await remoteClient.setReceiver(receiver)

        toServer.acceptValue(Value(123), Path.of("a", "b"))

        await sleep(0.1)
        self.assertIsNotNone(receiver.received)
        if receiver.received is None: return
        receivedTree, receivedPath = receiver.received
        self.assertEqual(receivedTree, ImmutableSampleTree.ofValue(Value(123)))
        self.assertEqual(receivedPath, Path.of("a", "b"))

        await toServer.close()
        await toClient.close()
        await server.close()
