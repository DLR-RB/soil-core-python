from asyncio import sleep
from typing import override
from unittest import IsolatedAsyncioTestCase

from soil.connection import HostedObservableStorage, RemoteObservableStorage
from soil.data import Path, SampleTree, Value
from soil.debug import PrintReceiver
from soil.encoding.json import JsonEncoding
from soil.framing import SyncByteLengthFraming
from soil.interfaces.tcp import TcpSocketClient, TcpSocketConnection, TcpSocketServer
from soil.logging import LogLevel
from soil.messaging import Message, MessageReceiver
from soil.requests import CompletedRequest, Request
from soil.storage import ObservingStorage

from ..util import TestStorage


class TcpSocketTest(IsolatedAsyncioTestCase):

    async def testRemoteStorageWriteRead(self):
        server = TcpSocketServer(port = 0)
        serverHandler = TestServer()

        server.onConnection(serverHandler.accept)

        self.assertTrue(await server.start())

        port = await server.waitForPort()
        self.assertGreaterEqual(port, 0)

        await sleep(0.01)

        path = Path.of("a", "b", "c")

        try:
            client = TcpSocketClient("localhost", port)
            socket = await client.connect()

            conn = await (await socket.apply(SyncByteLengthFraming())).apply(JsonEncoding())

            remote = await RemoteObservableStorage.create(conn)

            await remote.acceptValue(Value(123), path)

            self.assertTrue(
                await serverHandler.storage.waitForWrite()
            )

            serverHandler.storage.resetWaiting()
            await remote.shutdown()
            await conn.close()
            await socket.close()

        except Exception as exc:
            self.fail(f"Failed to create client or write: {exc}")

        samples = await serverHandler.storage.samples(path)

        self.assertIsNotNone(samples)
        self.assertFalse(len(samples) == 0)
        self.assertEqual(samples[0].value, Value(123))

        try:
            client = TcpSocketClient("localhost", port)
            socket = await client.connect()

            conn = await (await socket.apply(SyncByteLengthFraming())).apply(JsonEncoding())

            remote = await RemoteObservableStorage.create(conn)

            tree: SampleTree = await remote.currentTree(path, 0)
            self.assertNotEqual(len(tree.samples), 0)

            sample = tree.samples[0]
            self.assertEqual(sample.value, Value(123))
            await remote.shutdown()
            await conn.close()
            await socket.close()

        except Exception as exc:
            self.fail(f"Failed to create client or read: {exc}")
        finally:
            self.assertTrue(await server.stop())
            await socket.close()

        await serverHandler.shutdown()

    async def testMultipleMessagesInterleaving(self):
        printer = PrintReceiver()

        logger = printer.loggerAtPath(LogLevel.DEBUG, Path.of())

        server = TcpSocketServer(port = 0)
        serverHandler = TestServer()

        server.onConnection(serverHandler.accept)

        self.assertTrue(await server.start())

        port = await server.waitForPort()
        self.assertGreaterEqual(port, 0)

        await sleep(1)

        client = TcpSocketClient("localhost", port)

        socket = await client.connect()
        connectionToServer = await (await socket.apply(SyncByteLengthFraming())).apply(JsonEncoding())

        counter = 0
        serverSocket: TcpSocketConnection | None = None
        while serverSocket is None:
            await sleep(0.1)
            serverSocket = serverHandler.getMostRecentConnection()
            counter += 1
            if counter > 20:
                self.fail("No connection made to the server")

        connectionToClient = await (await serverSocket.apply(SyncByteLengthFraming(), logger)).apply(JsonEncoding(), logger)

        counter = ReceptionCounter()
        await connectionToClient.setReceiver(counter)
        await connectionToServer.acceptValue(
            Value(
                "Some very long string that takes a while to send "
                "so that the messages may overlap"
            ),
            Path.of("some", "longer", "path"),
        )

        await connectionToServer.acceptValue(
            Value("More text to test"),
            Path.of("another", "path"),
        )

        await connectionToServer.acceptValue(
            Value(123),
            Path.of("some", "number"),
        )

        await connectionToServer.acceptValue(Value("Even more"), Path.of("more"))

        await server.stop()
        await serverHandler.shutdown()
        await connectionToServer.close()


class ReceptionCounter(MessageReceiver):

    def __init__(self):
        self.counter = 0

    @override
    def acceptMessage(self, message: Message) -> Request:
        self.counter += 1
        return CompletedRequest()


class TestServer:

    def __init__(self):
        self.storage = TestStorage()

        self._clients: list[TcpSocketConnection] = []
        self._storages: list[HostedObservableStorage] = []

    async def accept(self, connection: TcpSocketConnection):
        messageConnection = await (await connection.apply(SyncByteLengthFraming())).apply(JsonEncoding())

        observableStorage = ObservingStorage(
            self.storage
        )

        clientConnection = await HostedObservableStorage.create(
            observableStorage,
            messageConnection,
        )

        self._storages.append(clientConnection)
        self._clients.append(connection)

    def getMostRecentConnection(self):
        if len(self._clients) == 0:
            return None
        return self._clients[-1]

    async def shutdown(self):
        for connection in self._clients:
            await connection.shutdown()
        for storage in self._storages:
            await storage.shutdown()
        await self.storage.shutdown()
