from typing import List, override

from ..utils import ByteRingBuffer, Actor

from .error import FramingError
from .framing import StreamFraming


class SyncByteLengthFraming(Actor, StreamFraming):
    """
    A framing implementation that uses sync bytes followed by a 2-byte
    length field to package messages into frames.

    Note:
        The maximum payload size is 65,535 bytes, which is the largest
        value that fits in the 2-byte length field.
    """

    def __init__(
        self,
        syncBytes: bytes | bytearray = b"\xAA\x55",
        maxPayloadLength: int = 65_535,
    ):
        """
        Create a framing processor.

        The internal receive buffer is sized to hold two complete frames,
        plus one additional byte.

        Args:
            syncBytes: The sync bytes identifying the start of each frame.
            maxPayloadLength: The maximum permitted payload size
                (0 < length <= 65,535).
        """
        Actor.__init__(self)

        if not syncBytes:
            raise ValueError("syncBytes cannot be empty")

        if maxPayloadLength <= 0:
            raise ValueError("maxPayloadLength must be > 0")

        if maxPayloadLength > 65_535:
            raise ValueError("maxPayloadLength must be <= 65,535")

        # The bytes identifying the start of a frame.
        self.syncBytes = bytes(syncBytes)

        # The maximum permitted payload size.
        self.maxPayloadLength = maxPayloadLength

        # The total header size (sync bytes + 2-byte length).
        self._headerSize = len(self.syncBytes) + 2

        # Ensure the ring buffer can hold two complete frames.
        ringBufferSize = (
            (maxPayloadLength + len(self.syncBytes) + 2) * 2
        ) + 1

        # Ring buffer holding received stream bytes.
        self._ring = ByteRingBuffer(ringBufferSize)

    @property
    def bufferedBytes(self) -> int:
        """
        The number of bytes currently stored in the receive buffer.
        """
        return self._ring.count

    # MARK: StreamFraming

    @override
    async def encodeForStream(self, message: bytes) -> bytes:
        """
        Add framing information (sync bytes and payload length) to a
        message, making it suitable for transmission over a binary stream.

        Args:
            message: The message to frame.

        Returns:
            The framed message.

        Raises:
            FramingError: If the payload exceeds the configured maximum.
        """
        message = bytes(message)

        if len(message) > self.maxPayloadLength:
            raise FramingError(FramingError.Code.payloadTooLarge)

        length = len(message)

        return (
            self.syncBytes
            + length.to_bytes(2, "big")
            + message
        )

    @override
    async def processStreamBytes(self, data: bytes) -> List[bytes]:
        """
        Extract framed messages from binary stream data.

        The decoder first searches for the sync bytes, then reads the
        following two-byte payload length, and finally extracts the
        payload.

        Args:
            data: Newly received stream bytes.

        Returns:
            A list of decoded payloads.
        """
        # TODO:
        # Write incoming data in chunks that fit into the ring buffer
        # to avoid overflow when very large inputs are supplied.
        self._ring.writeContentsOf(data)

        messages: list[bytes] = []

        # TODO:
        # Introduce explicit decoder state so sync bytes and payload
        # length do not need to be rediscovered each time new bytes
        # arrive.

        while True:
            # Need enough bytes for the complete frame header.
            if self._ring.count < self._headerSize:
                break

            # Find the sync sequence.
            syncOffset = self._ring.findSequence(self.syncBytes)

            if syncOffset is None:
                # No sync sequence exists in the buffer, so discard
                # everything.
                self._ring.clear()
                break

            # Discard bytes preceding the sync sequence.
            if syncOffset > 0:
                self._ring.discard(syncOffset)

            if self._ring.count < self._headerSize:
                break

            # Read the payload length.
            msb = self._ring.peek(len(self.syncBytes))
            lsb = self._ring.peek(len(self.syncBytes) + 1)
            length = (msb << 8) | lsb

            # Invalid length. Discard one byte and continue searching
            # for a valid frame.
            if length > self.maxPayloadLength:
                self._ring.discard(1)
                continue

            # Wait for the complete payload.
            if self._ring.count < self._headerSize + length:
                break

            # Skip the header.
            self._ring.discard(self._headerSize)

            # Read the payload.
            payload = self._ring.read(length)
            messages.append(payload)

        return messages
