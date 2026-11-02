import unittest
from contextlib import redirect_stdout
from io import StringIO

from soil.framing.logger import LoggingFraming
from soil.framing.sync import SyncByteLengthFraming


class TestLoggingFraming(unittest.IsolatedAsyncioTestCase):

    async def test_EncodePassthrough(self):
        framing = LoggingFraming()

        log = StringIO()
        with redirect_stdout(log):
            framed = await framing.encodeForStream(b'\x01\x02\x03')

        expected = await SyncByteLengthFraming().encodeForStream(b'\x01\x02\x03')
        self.assertEqual(framed, expected)

    async def test_ProcessPassthrough(self):
        framing = LoggingFraming()

        framed = await SyncByteLengthFraming().encodeForStream(b'hello')
        log = StringIO()
        with redirect_stdout(log):
            self.assertEqual(await framing.processStreamBytes(framed), [b'hello'])

    async def test_EncodeLogsHex(self):
        framing = LoggingFraming()

        log = StringIO()
        with redirect_stdout(log):
            framed = await framing.encodeForStream(b'\x01\x02\x03')

        self.assertIn(framed.hex(), log.getvalue())

    async def test_ProcessLogsHex(self):
        framing = LoggingFraming()

        framed = await SyncByteLengthFraming().encodeForStream(b'hello')
        log = StringIO()
        with redirect_stdout(log):
            payloads = await framing.processStreamBytes(framed)

        self.assertEqual(payloads, [b'hello'])
        self.assertIn(b'hello'.hex(), log.getvalue())

    async def test_MultipleFrames(self):
        framing = LoggingFraming()
        base = SyncByteLengthFraming()

        framed = await base.encodeForStream(b'a') + await base.encodeForStream(b'b')
        log = StringIO()
        with redirect_stdout(log):
            self.assertEqual(await framing.processStreamBytes(framed), [b'a', b'b'])