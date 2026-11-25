import asyncio

from soil.data import Path, SampleTree, Value
from soil.encoding.json import JsonEncoding
from soil.interfaces.udp import UdpSocket
from soil.messaging import Message, MessageReceiver, MessageType


class TelemetryCollector(MessageReceiver):
    """Stores the newest sample seen at each path."""

    def __init__(self):
        self.data = SampleTree()
        self.seen = 0

    async def acceptMessage(self, message: Message) -> None:
        if message.type == MessageType.DATA:
            self.data.mergeAtPath(message.data, message.path)
            self.seen += 1
            print(f"Telemetry: {message.path} = {message.data.newestSample.value.value}")


async def main():
    # UDP has no server — just a socket that both sides share.
    # The receiver answers any inbound datagram, so it uses onConnection()
    # to wrap a fresh connection and install its decoder + receiver.
    collector = TelemetryCollector()

    async def handle_incoming(connection):
        decoded = await connection.apply(JsonEncoding())
        await decoded.setReceiver(collector)

    receiver = UdpSocket(localPort=8080)
    receiver.onConnection(handle_incoming)
    await receiver.ready()

    # The sender (on this or another machine).
    sender = UdpSocket(localPort=0)
    await sender.ready()
    sender_conn = sender.connect("127.0.0.1", 8080)
    encoded = await sender_conn.apply(JsonEncoding())

    for value in [21.5, 22.1, 23.0]:
        await encoded.send(Message.value(Value(value), Path.of("sensor", "temperature")))
        await asyncio.sleep(0.05)

    # Wait until the collector has seen all values (UDP is lossy, so poll).
    for _ in range(50):
        if collector.seen >= 3:
            break
        await asyncio.sleep(0.05)

    print(f"Received {collector.seen} telemetry messages")

    receiver.close()
    sender.close()


if __name__ == "__main__":
    asyncio.run(main())
