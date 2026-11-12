import asyncio

from soil.components.receiver import Receiver
from soil.connection import HostedObservableStorage, RemoteObservableStorage
from soil.data import Path, SampleTree, Value
from soil.encoding.json import JsonEncoding
from soil.framing import SyncByteLengthFraming
from soil.interfaces.tcp import TcpSocketClient, TcpSocketServer
from soil.messaging import Message
from soil.requests import CompletedRequest, Request
from soil.storage import InMemoryStorage, ObservingStorage


# -- Server: a storage that can be subscribed to -- #
async def handle_server_connection(connection):
    framed = await connection.apply(SyncByteLengthFraming())
    decoded = await framed.apply(JsonEncoding())
    storage = ObservingStorage(InMemoryStorage())
    await HostedObservableStorage.create(storage, decoded)
    # Publish a value now that clients can subscribe to it.
    await asyncio.sleep(0.2)
    await decoded.send(Message.value(Value(25.0), Path.of("weather", "temperature")))
    return storage


# -- Client: collect updates that match the subscription -- #
class UpdateCollector(Receiver):
    def __init__(self):
        self.values = []

    def accept(self, tree: SampleTree, path: Path = Path()) -> Request:
        node = tree.existingNode(Path.of("weather", "temperature"))
        sample = node.newestSample if node is not None else tree.newestSample
        if sample is None:
            return CompletedRequest()
        self.values.append(str(sample.value.value))
        print(f"Subscribed update: {sample.value.value}")
        return CompletedRequest()


async def main():
    server = TcpSocketServer(port=0)

    async def handle_connection(connection):
        await handle_server_connection(connection)

    server.onConnection(handle_connection)
    assert await server.start()
    port = await server.waitForPort()

    client = TcpSocketClient("localhost", port)
    stream = await client.connect()
    framed = await stream.apply(SyncByteLengthFraming())
    decoded = await framed.apply(JsonEncoding())

    remote = await RemoteObservableStorage.create(decoded)

    collector = UpdateCollector()
    await remote.setReceiver(collector)

    # Choose which data to receive.
    await remote.include(Path.of("weather"), depth=2)
    await remote.exclude(Path.of("weather", "humidity"), depth=1)

    await asyncio.sleep(0.5)  # wait for the published update to arrive
    print(f"Collected {len(collector.values)} updates")
    await decoded.close()
    assert await server.stop()


if __name__ == "__main__":
    asyncio.run(main())

