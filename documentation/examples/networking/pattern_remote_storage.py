import asyncio

from soil.connection import HostedStorage, RemoteStorage
from soil.data import Path, SampleTree, Value
from soil.encoding.json import JsonEncoding
from soil.framing import SyncByteLengthFraming
from soil.interfaces.tcp import TcpSocketClient, TcpSocketServer
from soil.storage import InMemoryStorage


async def main():
    server = TcpSocketServer(port=0)

    async def handle_connection(connection):
        framed = await connection.apply(SyncByteLengthFraming())
        decoded = await framed.apply(JsonEncoding())
        # Expose a local storage over the connection.
        await HostedStorage.create(InMemoryStorage(), decoded)

    server.onConnection(handle_connection)
    assert await server.start()
    port = await server.waitForPort()

    client = TcpSocketClient("localhost", port)
    stream = await client.connect()
    framed = await stream.apply(SyncByteLengthFraming())
    decoded = await framed.apply(JsonEncoding())

    remote = await RemoteStorage.create(decoded)

    # Write a value to the remote storage.
    await remote.accept(SampleTree.ofValue(Value(21.5), timestamp=None), Path.of("weather", "temperature"))
    await asyncio.sleep(0.1)

    # Read it back. Request the exact path, so the sample is returned at the tree root.
    tree = await remote.tree(Path.of("weather", "temperature"), start=None, end=None, depth=None, limitPerNode=None)
    sample = tree.newestSample
    value = str(sample.value.value) if sample else "n/a"
    print(f"Remote value: {value}")

    await decoded.close()
    assert await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
