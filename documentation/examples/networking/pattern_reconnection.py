import asyncio

from soil.connection import ReconnectingConnection
from soil.data import Path, SampleTree, Value
from soil.encoding.json import JsonEncoding
from soil.framing import SyncByteLengthFraming
from soil.interfaces.tcp import TcpSocketClient, TcpSocketServer
from soil.messaging import Message, MessageReceiver, MessageType


async def make_connect(port: int):
    """Factory: build a fresh decoded connection to the server at a given port."""
    async def connect():
        client = TcpSocketClient("127.0.0.1", port)
        stream = await client.connect()
        framed = await stream.apply(SyncByteLengthFraming())
        return await framed.apply(JsonEncoding())
    return connect


# -- Server side: print whatever arrives over each new connection -- #
class PrintReceiver(MessageReceiver):
    async def acceptMessage(self, message: Message):
        if message.type == MessageType.DATA:
            sample = message.data.newestSample
            value = str(sample.value.value) if sample else "n/a"
            print(f"Server received [{message.path}] = {value}")


async def main():
    server = TcpSocketServer(port=0)

    async def handle_connection(connection):
        framed = await connection.apply(SyncByteLengthFraming())
        decoded = await framed.apply(JsonEncoding())
        await decoded.setReceiver(PrintReceiver())

    server.onConnection(handle_connection)
    assert await server.start()

    # The server starts on port 0, so we set the real port before connecting.
    port = await server.waitForPort()

    connect = await make_connect(port)
    reconnection = ReconnectingConnection(connect, retryInterval=0.1)
    reconnection.start()

    # Send through the reconnection wrapper.
    message = Message.tree(SampleTree.ofValue(Value(42)), Path.of("data"))
    reconnection.send(message)

    await asyncio.sleep(0.3)

    reconnection.stop()
    assert await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
