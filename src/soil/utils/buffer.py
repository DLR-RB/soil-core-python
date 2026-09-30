from collections.abc import Iterable


class ByteRingBuffer:
    """
    A ring buffer to store bytes of a binary stream.
    """

    def __init__(self, capacity: int, overwriteWhenFull: bool = True):
        """
        Create a ring buffer to store bytes.

        Args:
            capacity: The size (in bytes) of the buffer. Must be greater than zero.
            overwriteWhenFull: If True, newly written bytes overwrite the oldest
                bytes when the buffer is full. Otherwise, new bytes are discarded.
        """
        if capacity <= 0:
            raise ValueError("Capacity must be > 0")

        # The raw storage for the ring buffer data.
        self._buffer = bytearray(capacity)

        # The index of the first element (if count > 0).
        self.head = 0

        # The index where the next element is inserted.
        self.tail = 0

        # The number of elements currently in the buffer.
        self.count = 0

        # The total capacity of the buffer.
        self.capacity = capacity

        # Indicates whether new bytes should overwrite the oldest bytes if
        # the buffer is full.
        self.overwriteWhenFull = overwriteWhenFull

    # MARK: Write

    def write(self, byte: int) -> None:
        """
        Insert a byte into the buffer.

        Args:
            byte: The byte to insert (0-255).

        Note:
            If the buffer is full and ``overwriteWhenFull`` is enabled,
            the oldest byte will be overwritten. Otherwise, the new byte
            will be discarded.
        """
        if not 0 <= byte <= 0xFF:
            raise ValueError("Byte must be in range 0-255")

        if self.count == self.capacity:

            if not self.overwriteWhenFull:
                return

            # Overwrite the oldest byte.
            self.head = (self.head + 1) % self.capacity
            self.count -= 1

        self._buffer[self.tail] = byte
        self.tail = (self.tail + 1) % self.capacity
        self.count += 1

    def writeContentsOf(self, sequence: Iterable[int]) -> None:
        """
        Insert a sequence of bytes into the buffer.

        Args:
            sequence: The bytes to insert.
        """
        for byte in sequence:
            self.write(byte)

    # MARK: Read

    def read(self, count: int) -> bytes:
        """
        Read a number of bytes.

        Args:
            count: The number of bytes to read.

        Returns:
            The requested bytes from the beginning of the buffer.

        Raises:
            ValueError: If there is insufficient data in the buffer.
        """
        if count > self.count:
            raise ValueError("Not enough data")

        out = bytearray(count)

        for i in range(count):
            out[i] = self._buffer[self.head]
            self.head = (self.head + 1) % self.capacity

        self.count -= count
        return bytes(out)

    # MARK: Discard

    def discard(self, count: int) -> None:
        """
        Discard a number of bytes.

        Args:
            count: The number of bytes to discard.

        Raises:
            ValueError: If there are insufficient bytes to discard.
        """
        if count > self.count:
            raise ValueError("Not enough data")

        self.head = (self.head + count) % self.capacity
        self.count -= count

    def clear(self) -> None:
        """
        Remove all bytes from the buffer.
        """
        self.head = 0
        self.tail = 0
        self.count = 0

    # MARK: Peek

    def peek(self, offset: int) -> int:
        """
        Check a byte at an offset without advancing the buffer.

        Args:
            offset: The offset from the beginning of the buffered data.

        Returns:
            The byte at the requested offset.

        Raises:
            ValueError: If the offset is outside the buffered data.
        """
        if offset >= self.count or offset < 0:
            raise ValueError("Offset out of range")

        return self._buffer[(self.head + offset) % self.capacity]

    # MARK: Search

    def findSequence(self, sequence: bytes | bytearray | Iterable[int]) -> int | None:
        """
        Find the first occurrence of a byte sequence.

        Args:
            sequence: The byte sequence to locate in the buffer.

        Returns:
            The offset where the sequence starts, or None if the sequence
            could not be found.
        """
        if not isinstance(sequence, (bytes, bytearray)):
            sequence = bytes(sequence)

        if not sequence:
            return None

        if self.count < len(sequence):
            return None

        for i in range(self.count - len(sequence) + 1):
            match = True
            for j, value in enumerate(sequence):
                if self.peek(i + j) != value:
                    match = False
                    break
            if match:
                return i

        return None
