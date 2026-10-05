import unittest

from soil.utils import ByteRingBuffer


class TestByteRingBuffer(unittest.TestCase):

    # MARK: Construction

    def test_RejectsNonPositiveCapacity(self):
        with self.assertRaises(ValueError):
            ByteRingBuffer(0)
        with self.assertRaises(ValueError):
            ByteRingBuffer(-1)

    # MARK: Write / Read

    def test_WriteAndRead(self):
        buffer = ByteRingBuffer(4)
        buffer.write(0x01)
        buffer.write(0x02)
        buffer.write(0x03)

        self.assertEqual(buffer.count, 3)
        self.assertEqual(buffer.read(3), bytes([0x01, 0x02, 0x03]))
        self.assertEqual(buffer.count, 0)

    def test_WriteRejectsInvalidByte(self):
        buffer = ByteRingBuffer(4)

        with self.assertRaises(ValueError):
            buffer.write(256)
        with self.assertRaises(ValueError):
            buffer.write(-1)

    def test_WriteContentsOf(self):
        buffer = ByteRingBuffer(4)
        buffer.writeContentsOf([0x01, 0x02, 0x03])

        self.assertEqual(buffer.read(3), bytes([0x01, 0x02, 0x03]))

    def test_ReadInsufficientDataRaises(self):
        buffer = ByteRingBuffer(4)
        buffer.write(0x01)

        with self.assertRaises(ValueError):
            buffer.read(2)

    def test_WraparoundPreservesOrder(self):
        buffer = ByteRingBuffer(3)
        buffer.write(0x01)
        buffer.write(0x02)
        self.assertEqual(buffer.read(1), bytes([0x01]))

        buffer.write(0x03)
        buffer.write(0x04)
        buffer.write(0x05)

        self.assertEqual(buffer.read(3), bytes([0x03, 0x04, 0x05]))

    # MARK: Overwrite

    def test_OverwriteWhenFull(self):
        buffer = ByteRingBuffer(3)
        buffer.writeContentsOf([0x01, 0x02, 0x03, 0x04])

        self.assertEqual(buffer.count, 3)
        self.assertEqual(buffer.read(3), bytes([0x02, 0x03, 0x04]))

    def test_DiscardNewBytesWhenFull(self):
        buffer = ByteRingBuffer(3, overwriteWhenFull=False)
        buffer.writeContentsOf([0x01, 0x02, 0x03])

        self.assertEqual(buffer.count, 3)
        buffer.write(0x04)

        self.assertEqual(buffer.count, 3)
        self.assertEqual(buffer.read(3), bytes([0x01, 0x02, 0x03]))

    # MARK: Discard / Clear

    def test_Discard(self):
        buffer = ByteRingBuffer(4)
        buffer.writeContentsOf([0x01, 0x02, 0x03, 0x04])
        buffer.discard(2)

        self.assertEqual(buffer.count, 2)
        self.assertEqual(buffer.read(2), bytes([0x03, 0x04]))

    def test_DiscardInsufficientDataRaises(self):
        buffer = ByteRingBuffer(4)
        buffer.write(0x01)

        with self.assertRaises(ValueError):
            buffer.discard(2)

    def test_Clear(self):
        buffer = ByteRingBuffer(4)
        buffer.writeContentsOf([0x01, 0x02, 0x03, 0x04])
        buffer.clear()

        self.assertEqual(buffer.count, 0)
        with self.assertRaises(ValueError):
            buffer.read(1)

    # MARK: Peek

    def test_PeekDoesNotAdvance(self):
        buffer = ByteRingBuffer(4)
        buffer.writeContentsOf([0x01, 0x02, 0x03])

        self.assertEqual(buffer.peek(0), 0x01)
        self.assertEqual(buffer.peek(2), 0x03)
        self.assertEqual(buffer.count, 3)
        self.assertEqual(buffer.read(3), bytes([0x01, 0x02, 0x03]))

    def test_PeekOutOfRangeRaises(self):
        buffer = ByteRingBuffer(4)
        buffer.write(0x01)

        with self.assertRaises(ValueError):
            buffer.peek(1)
        with self.assertRaises(ValueError):
            buffer.peek(-1)

    def test_PeekAfterWraparound(self):
        buffer = ByteRingBuffer(3)
        buffer.writeContentsOf([0x01, 0x02])
        buffer.read(1)
        buffer.writeContentsOf([0x03, 0x04, 0x05])

        self.assertEqual(buffer.peek(0), 0x03)
        self.assertEqual(buffer.peek(2), 0x05)

    # MARK: Search

    def test_FindSequence(self):
        buffer = ByteRingBuffer(8)
        buffer.writeContentsOf([0x01, 0x02, 0x03, 0x04])

        self.assertEqual(buffer.findSequence(bytes([0x02, 0x03])), 1)
        self.assertEqual(buffer.findSequence(bytes([0x04])), 3)
        self.assertEqual(buffer.findSequence(bytes([0x01, 0x04])), None)

    def test_FindSequenceAcrossWraparound(self):
        buffer = ByteRingBuffer(3)
        buffer.writeContentsOf([0x01, 0x02])
        buffer.read(1)
        buffer.writeContentsOf([0x03, 0x04, 0x05])

        self.assertEqual(buffer.findSequence(bytes([0x03, 0x04])), 0)
        self.assertEqual(buffer.findSequence(bytes([0x04, 0x05])), 1)

    def test_FindSequenceNotFoundAndEmpty(self):
        buffer = ByteRingBuffer(2)
        buffer.writeContentsOf([0x01, 0x02])

        self.assertIsNone(buffer.findSequence(bytes([0x01, 0x02, 0x03])))
        self.assertIsNone(buffer.findSequence(bytes()))

    def test_FindSequenceAcceptsIterables(self):
        buffer = ByteRingBuffer(4)
        buffer.writeContentsOf([0x01, 0x02, 0x03])

        self.assertEqual(buffer.findSequence([0x02, 0x03]), 1)
        self.assertEqual(buffer.findSequence((x for x in [0x03])), 2)