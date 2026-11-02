import unittest

from soil.data import Path
from soil.data.value import Value
from soil.framing.connection import FrameConnection
from soil.messaging.decoded import DecodedConnection
from soil.messaging.encoding import MessageEncoding
from soil.messaging.message import Message
from soil.messaging.receiver import MessageReceiver
from soil.utils.actor import Actor


class StubFrameConnection(FrameConnection):
    """ Frame-Verbindung, die Aufrufe mitzeichnet. """

    def __init__(self):
        self.frameReceiver = None
        self.sent = []
        self.open = True
        self.onCloseCalls = []

    async def setReceiver(self, receiver):
        self.frameReceiver = receiver

    async def send(self, data):
        self.sent.append(data)

    async def isOpen(self):
        return self.open

    async def close(self):
        self.open = False

    async def onClose(self, perform):
        self.onCloseCalls.append(perform)

    def getReceiver(self):  
        return self.frameReceiver


class StubEncoding(MessageEncoding):
    """ Encoding mit steuerbaren Fehlern. """

    def __init__(self, failDecode=False, failEncode=False):
        self.failDecode = failDecode
        self.failEncode = failEncode
        self.encodedMessages = []
        self.decodedFrames = []

    def encode(self, message):
        if self.failEncode:
            raise ValueError("encode failed")
        self.encodedMessages.append(message)
        return b"encoded"

    def decode(self, frame):
        if self.failDecode:
            raise ValueError("decode failed")
        self.decodedFrames.append(frame)
        return Message.value(Value(1), Path.of("a"))


class StubMessageReceiver(MessageReceiver):
    """ Receiver, der Messages mitzeichnet. """

    def __init__(self):
        self.received = []

    async def acceptMessage(self, message):
        self.received.append(message)


class StubActorEncoding(Actor, MessageEncoding):
    """ Encoding auf Actor-Basis, um den Shutdown-Pfad zu testen. """

    def __init__(self):
        Actor.__init__(self)
        self.shutDown = False

    async def shutdown(self):
        self.shutDown = True

    def encode(self, message):
        return b"encoded"

    def decode(self, frame):
        return Message()

    

class TestDecodedConnection(unittest.IsolatedAsyncioTestCase):

    async def test_InitializeSetsFrameReceiver(self):
        frameConnection = StubFrameConnection()
        connection = DecodedConnection(frameConnection, StubEncoding())

        await connection.initialize()

        self.assertIs(frameConnection.frameReceiver, connection)

    async def test_CreateReturnsInitializedConnection(self):
        frameConnection = StubFrameConnection()

        connection = await DecodedConnection.create(
            frameConnection,
            StubEncoding(),
        )

        self.assertIs(frameConnection.frameReceiver, connection)

    async def test_SendEncodesAndForwards(self):
        frameConnection = StubFrameConnection()
        encoding = StubEncoding()
        connection = DecodedConnection(frameConnection, encoding)
        message = Message()

        await connection.send(message)

        self.assertEqual(encoding.encodedMessages, [message])
        self.assertEqual(frameConnection.sent, [b"encoded"])

    async def test_SendWithEncodeErrorSendsNothing(self):
        frameConnection = StubFrameConnection()
        connection = DecodedConnection(frameConnection, StubEncoding(failEncode=True))

        await connection.send(Message())

        self.assertEqual(frameConnection.sent, [])

    async def test_AcceptFrameBeforeReceiverBuffersFrame(self):
        frameConnection = StubFrameConnection()
        encoding = StubEncoding()
        connection = DecodedConnection(frameConnection, encoding)

        await connection.acceptFrame(b"frame1")
        await connection.acceptFrame(b"frame2")

        self.assertIsNone(await connection.getReceiver())
        self.assertEqual(encoding.decodedFrames, [])

    async def test_SetReceiverFlushesPendingFrames(self):
        frameConnection = StubFrameConnection()
        encoding = StubEncoding()
        connection = DecodedConnection(frameConnection, encoding)
        receiver = StubMessageReceiver()

        await connection.acceptFrame(b"frame1")
        await connection.acceptFrame(b"frame2")
        await connection.setReceiver(receiver)

        self.assertEqual(encoding.decodedFrames, [b"frame1", b"frame2"])
        self.assertEqual(len(receiver.received), 2)

    async def test_SetReceiverWithFailingFrameContinues(self):
        frameConnection = StubFrameConnection()
        encoding = StubEncoding(failDecode=True)
        connection = DecodedConnection(frameConnection, encoding)
        receiver = StubMessageReceiver()

        await connection.acceptFrame(b"bad1")
        await connection.acceptFrame(b"bad2")
        await connection.setReceiver(receiver)

        self.assertEqual(receiver.received, [])

    async def test_AcceptFrameForwardsDecodedMessage(self):
        frameConnection = StubFrameConnection()
        encoding = StubEncoding()
        connection = DecodedConnection(frameConnection, encoding)
        receiver = StubMessageReceiver()
        await connection.setReceiver(receiver)

        await connection.acceptFrame(b"frame")

        self.assertEqual(encoding.decodedFrames, [b"frame"])
        self.assertEqual(len(receiver.received), 1)

    async def test_AcceptFrameWithDecodeErrorForwardsNothing(self):
        frameConnection = StubFrameConnection()
        connection = DecodedConnection(frameConnection, StubEncoding(failDecode=True))
        receiver = StubMessageReceiver()
        await connection.setReceiver(receiver)

        await connection.acceptFrame(b"bad")

        self.assertEqual(receiver.received, [])

    async def test_GetReceiver(self):
        frameConnection = StubFrameConnection()
        connection = DecodedConnection(frameConnection, StubEncoding())
        receiver = StubMessageReceiver()

        self.assertIsNone(await connection.getReceiver())
        await connection.setReceiver(receiver)
        result = await connection.getReceiver()
        self.assertIs(result, receiver)

    async def test_IsOpenDelegatesToConnection(self):
        frameConnection = StubFrameConnection()
        connection = DecodedConnection(frameConnection, StubEncoding())

        self.assertTrue(await connection.isOpen())
        frameConnection.open = False
        self.assertFalse(await connection.isOpen())

    async def test_CloseClosesUnderlyingConnection(self):
        frameConnection = StubFrameConnection()
        connection = DecodedConnection(frameConnection, StubEncoding())

        await connection.close()

        self.assertFalse(frameConnection.open)

    async def test_CloseShutsDownActorEncoding(self):
        frameConnection = StubFrameConnection()
        encoding = StubActorEncoding()
        connection = DecodedConnection(frameConnection, encoding)

        await connection.close()

        self.assertTrue(encoding.shutDown)
        self.assertFalse(frameConnection.open)

    async def test_OnCloseForwardsPerform(self):
        frameConnection = StubFrameConnection()
        connection = DecodedConnection(frameConnection, StubEncoding())

        performed = []
        await connection.onClose(lambda: performed.append(True))

        self.assertEqual(len(frameConnection.onCloseCalls), 1)