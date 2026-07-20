from typing import override
from unittest import main

from soil.components import Receiver
from soil.connection import DataMessageSplitter, RemoteTransmitter
from soil.encoding import JsonEncoding
from soil.messaging import MessageReceiver, Message
from soil.data import ImmutableSampleTree, Path, Sample, SampleTree, Timestamp, Value
from soil.utils import Actor, synchronized, queuedAsync

from ..util import SoilAsyncTest, TestConnection


class TestMessageReceiver(Actor, MessageReceiver):
    """ Test implementation of MessageReceiver that counts received messages. """

    def __init__(self):
        Actor.__init__(self)
        self._count = 0

    @override
    @synchronized
    async def acceptMessage(self, message: Message) -> None:
        self._count += 1

    @queuedAsync
    def getCount(self) -> int:
        return self._count


class TestReceiver(Actor, Receiver):
    """ Test receiver that stores the last received tree and path. """

    def __init__(self):
        Actor.__init__(self)
        self._count = 0
        self._last: tuple[SampleTree, Path] | None = None

    @override
    @synchronized
    async def accept(
        self,
        tree: SampleTree,
        path: Path,
    ) -> None:
        self._count += 1
        self._last = (tree, path)

    @queuedAsync
    def getCount(self) -> int:
        return self._count

    @queuedAsync
    def getLast(self) -> tuple[SampleTree, Path] | None:
        return self._last


class DataMessageSplitterTest(SoilAsyncTest):

    async def testSplitTree(self):
        """Split a tree into individual messages."""

        tree = ImmutableSampleTree(
            samples=[ Sample(value=Value("a"), timestamp=Timestamp.fromTimeIntervalSince1970(1.0)) ],
            children = {
                "b": ImmutableSampleTree(
                    samples = [
                        Sample(value=Value("b"), timestamp=Timestamp.fromTimeIntervalSince1970(2))
                    ],
                    children = {
                        "c": ImmutableSampleTree.ofValue(
                            value=Value("c"),
                            timestamp=Timestamp.fromTimeIntervalSince1970(3),
                        )
                    },
                ),
                "d": ImmutableSampleTree.ofValue(
                    value=Value("d"),
                    timestamp=Timestamp.fromTimeIntervalSince1970(4)
                )
            },
        )

        one, two = await TestConnection.create()
        connection = await one.apply(JsonEncoding())
        receivingConnection = await two.apply(JsonEncoding())

        receiver = TestMessageReceiver()
        await receivingConnection.setReceiver(receiver).wait()

        splitter = await DataMessageSplitter.create(connection)

        await splitter.send(Message.tree(tree, Path.of("xyz"))).wait()
        self.assertEqual(await receiver.getCount(), 4)

    async def testSplitBatchCorrectly(self):
        """ Send separate messages of a batch to the splitter, and recombine them """

        tree = ImmutableSampleTree(
            samples=[
                Sample(value = Value("a"), timestamp = Timestamp.fromTimeIntervalSince1970(1.0))
            ],
            children={
                "b": ImmutableSampleTree(
                    samples = [
                        Sample(value = Value("b"), timestamp = Timestamp.fromTimeIntervalSince1970(2))
                    ],
                    children={
                        "c": ImmutableSampleTree.ofValue(
                            value = Value("c"),
                            timestamp = Timestamp.fromTimeIntervalSince1970(3),
                        )
                    },
                ),
                "d": ImmutableSampleTree.ofValue(
                    value = Value("d"),
                    timestamp = Timestamp.fromTimeIntervalSince1970(4),
                ),
            },
        )

        one, two = await TestConnection.create()

        # Create the connection that sends the batched messages.
        connection = await one.apply(JsonEncoding())

        splitter = await DataMessageSplitter.create(connection)

        # Create the receiver that recombines them.
        receivingConnection = await two.apply(JsonEncoding())
        receiver = TestReceiver()
        combiner = await RemoteTransmitter.create(
            receiver=receiver,
            connection=receivingConnection,
            batchTimeout=1.5,
        )

        path = Path.of("xyz")

        # Send the samples of A
        treeA = ImmutableSampleTree(samples = tree.samples)
        await splitter.send(Message.tree(treeA, path = path, request = 123, totalMessages = 3)).wait()

        # Send the tree at B, including C
        await splitter.send(Message.tree(tree.children["b"], path + ["b"], request = 123, totalMessages = 3)).wait()

        # Send D
        await splitter.send(Message.tree(tree.children["d"], path + ["d"], request = 123, totalMessages = 3)).wait()

        self.assertEqual(await receiver.getCount(), 1)

        received = await receiver.getLast()
        self.assertIsNotNone(received)
        if received is None: return

        receivedTree, receivedPath = received

        self.assertEqual(receivedPath, path)
        self.assertTrue(receivedTree.isEqualTo(tree))

        # Keep a reference so the object isn't optimized away.
        await combiner.setReceiver(receiver).wait()

    async def testRecombineMessages(self):
        """Recombine split messages into a single tree."""

        tree = ImmutableSampleTree(
            samples=[
                Sample(value = Value("a"), timestamp = Timestamp.fromTimeIntervalSince1970(1.0))
            ],
            children={
                "b": ImmutableSampleTree(
                    samples = [
                        Sample(value = Value("b"), timestamp = Timestamp.fromTimeIntervalSince1970(2))
                    ],
                    children={
                        "c": ImmutableSampleTree.ofValue(
                            value = Value("c"),
                            timestamp = Timestamp.fromTimeIntervalSince1970(3),
                        )
                    },
                ),
                "d": ImmutableSampleTree.ofValue(
                    value = Value("d"),
                    timestamp = Timestamp.fromTimeIntervalSince1970(4),
                ),
            },
        )

        one, two = await TestConnection.create()

        # Create the connection that sends the batched messages.
        connection = await one.apply(
            encoding=JsonEncoding()
        )

        splitter = await DataMessageSplitter.create(connection)

        # Create the receiver that recombines them.
        receivingConnection = await two.apply(
            encoding=JsonEncoding()
        )

        receiver = TestReceiver()

        combiner = await RemoteTransmitter.create(
            receiver=receiver,
            connection=receivingConnection,
            batchTimeout=1.5,
        )

        path = Path.of("xyz")

        await splitter.send(Message.tree(tree, path)).wait()
        self.assertEqual(await receiver.getCount(), 1)

        received = await receiver.getLast()
        self.assertIsNotNone(received)
        if received is None: return

        receivedTree, receivedPath = received

        self.assertEqual(receivedPath, path)
        self.assertTrue(receivedTree.isEqualTo(tree))

        # Keep a reference so the object isn't optimized away.
        await combiner.setReceiver(receiver).wait()


if __name__ == "__main__":
    main()
