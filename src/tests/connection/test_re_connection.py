import unittest

from asyncio import sleep

from soil.data import Path, SampleTree, Sample
from soil.data.value import Value
from soil.messaging import Message, MessageConnection
from soil.requests import CompletedRequest

from soil.connection.re_connection import ReconnectingConnection



class MockConnection(MessageConnection):

    def __init__(self):
        self.sent = []             
        self.hasReceiver  = False  
        self.open = True       
        self.closed = False 
        self.receiver = None

    def send(self, message):
        self.sent.append(message)
        return CompletedRequest()

    def setReceiver(self, receiver):
        self.hasReceiver = True
        self.receiver = receiver
        return CompletedRequest()

    async def getReceiver(self):
        return None

    async def isOpen(self):
        return self.open and not self.closed

    def close(self):
        self.closed = True
        return CompletedRequest()

    def onClose(self, perform):
        return CompletedRequest()

    
class TestReConnection(unittest.IsolatedAsyncioTestCase):

    async def waitUntil(self, condition):
        """ Wait until condition() becomes True (checks every 10 ms). """
        for _ in range(200):
            if condition():
                return
            await sleep(0.01)
        self.fail("Timed out waiting for condition")


    async def test_Start(self):
        connection = MockConnection()

        async def connect():
            return connection

        re_con = ReconnectingConnection(connect, retryInterval=0.01)
        self.addAsyncCleanup(re_con.stop)


        re_con.start()

        await self.waitUntil(lambda: connection.hasReceiver)


    async def test_Send(self):
        connection = MockConnection()

        async def connect():
            return connection

        re_con = ReconnectingConnection(connect, retryInterval=0.01)
        self.addAsyncCleanup(re_con.stop)

        re_con.start()
        await self.waitUntil(lambda: connection.hasReceiver)

        message = Message.tree(SampleTree([Sample(Value(1))]), Path("a"))
        re_con.send(message)

        await self.waitUntil(lambda: len(connection.sent) == 1)
        self.assertIs(connection.sent[0], message)


    async def test_Stop(self):
        connection = MockConnection()

        async def connect():
            return connection

        re_con = ReconnectingConnection(connect, retryInterval=0.01)

        onCloseCalls = []
        re_con.onClose(lambda: onCloseCalls.append(1))

        re_con.start()
        await self.waitUntil(lambda: connection.hasReceiver) 

        re_con.stop()

        self.assertTrue(connection.closed)
        self.assertEqual(len(onCloseCalls), 1)
        self.assertFalse(await re_con.isOpen())


    async def test_SetGetReceiver(self):
        connection = MockConnection()

        async def connect():
            return connection

        re_con = ReconnectingConnection(connect, retryInterval=0.01)
        self.addAsyncCleanup(re_con.stop)

        re_con.setReceiver("my receiver")

        self.assertIs(await re_con.getReceiver(), "my receiver")



    async def test_IsOpenBeforeConnection(self):
        connection = MockConnection()

        async def connect():
            return connection

        re_con = ReconnectingConnection(connect, retryInterval=0.01)
        self.addAsyncCleanup(re_con.stop)

        self.assertFalse(await re_con.isOpen())


    async def test_IsOpenFollowsConnection(self):
        connection = MockConnection()

        async def connect():
            return connection

        re_con = ReconnectingConnection(connect, retryInterval=0.01)
        self.addAsyncCleanup(re_con.stop)

        re_con.start()
        await self.waitUntil(lambda: connection.hasReceiver)

        self.assertTrue(await re_con.isOpen())

        connection.open = False
        self.assertFalse(await re_con.isOpen())


    async def test_SendBeforeConnectionIsQueued(self):
        connection = MockConnection()
        count = [0]

        async def connect():
            count[0] += 1
            if count[0] == 1:
                return None
            return connection

        re_con = ReconnectingConnection(connect, retryInterval=0.01)
        self.addAsyncCleanup(re_con.stop)

        message = Message.tree(SampleTree([Sample(Value(1))]), Path("a"))
        re_con.send(message)

        re_con.start()

        await self.waitUntil(lambda: len(connection.sent) == 1)



    async def test_ReconnectsAfterDrop(self):
        connection1 = MockConnection()
        connection2 = MockConnection()
        calls = 0

        async def connect():
            nonlocal calls
            calls += 1
            if calls == 1:
                return connection1
            return connection2        

        re_con = ReconnectingConnection(connect, retryInterval=0.01)
        self.addAsyncCleanup(re_con.stop)

        re_con.start()
        await self.waitUntil(lambda: connection1.hasReceiver)   

        connection1.open = False    

        await self.waitUntil(lambda: connection2.hasReceiver)  
        self.assertTrue(connection1.closed)  

        message = Message.tree(SampleTree([Sample(Value(1))]), Path("a"))
        re_con.send(message)
        await self.waitUntil(lambda: len(connection2.sent) == 1)


