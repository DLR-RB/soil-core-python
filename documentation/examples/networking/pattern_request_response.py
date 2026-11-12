import asyncio

from soil.data import Path, SampleTree, Value
from soil.encoding.json import JsonEncoding
from soil.framing import SyncByteLengthFraming
from soil.interfaces.tcp import TcpSocketClient, TcpSocketServer
from soil.messaging import Message, MessageReceiver, MessageType
from soil.requests import CompletedRequest


# -- Server: remember received values, reply to read requests -- #
class WeatherServer(MessageReceiver):
    def __init__(self):
        self.data = SampleTree()

    def acceptMessage(self, message: Message) -> CompletedRequest:
        if message.type == MessageType.REQUEST:
            node = self.data.existingNode(message.path)
            samples = node.getSamples(message.time, message.end, message.count) if node else []
            asyncio.ensure_future(
                self.connection.send(
                    Message.samples(samples, message.path, request=message.id, totalMessages=1)
                )
            )
        elif message.type == MessageType.DATA:
            self.data.mergeAtPath(message.data, message.path)
        return CompletedRequest()


# -- Client: remember only the response whose id matches the request -- #
class ResponseCollector(MessageReceiver):
    def __init__(self, request_id: int):
        self.request_id = request_id
        self.response = None

    async def acceptMessage(self, message: Message) -> CompletedRequest:
        if message.type == MessageType.DATA and message.id == self.request_id:
            self.response = message
        return CompletedRequest()


async def main():
    server = TcpSocketServer(port=0)

    async def handle_connection(connection):
        framed = await connection.apply(SyncByteLengthFraming())
        decoded = await framed.apply(JsonEncoding())
        server_obj = WeatherServer()
        server_obj.connection = decoded
        await decoded.setReceiver(server_obj)

    server.onConnection(handle_connection)
    assert await server.start()
    port = await server.waitForPort()

    client = TcpSocketClient("localhost", port)
    stream = await client.connect()
    framed = await stream.apply(SyncByteLengthFraming())
    connection = await framed.apply(JsonEncoding())

    collector = ResponseCollector(request_id=1)
    await connection.setReceiver(collector)

    # Seed the server with values (DATA messages are stored by path).
    await connection.send(Message.value(Value(21.5), Path.of("temperature")))
    await connection.send(Message.value(Value(63), Path.of("humidity")))

    # Read a value back from the server.
    await connection.send(Message.request(Path.of("temperature"), id=1))
    await asyncio.sleep(0.2)  # give the round-trip time to complete

    if collector.response:
        # The response carries the requested samples at its root,
        # and the requested path in `message.path`.
        sample = collector.response.data.newestSample
        value = str(sample.value.value) if sample else "n/a"
        print(f"Received value: {value}")
    else:
        print("No response received")

    await connection.shutdown()
    assert await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
