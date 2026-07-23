from abc import abstractmethod

from ..components import Connection
from ..framing import FrameConnection, StreamFraming
from ..logging import Logger
from ..requests import Request

from .decoded import DecodedStream
from .distributor import StreamDistributor


class StreamConnection(Connection, StreamDistributor):
    """
    A connection to a component that transmits and receives frames.
    """

    @abstractmethod
    def send(self, bytes: bytes | bytearray) -> Request:
        """
        Send bytes to the component via the underlying transport layer.

        Args:
            bytes: The bytes to send.

        Returns:
            The transmission request, which can optionally be awaited to
            wait for transmission.

        Note:
            The returned request waits only for transmission by the
            transport layer. It does not wait for the message to be
            delivered to the remote endpoint.
        """
        raise NotImplementedError

    async def apply(
        self,
        framing: StreamFraming,
        logger: Logger | None = None,
    ) -> FrameConnection:
        """
        Convert this stream to a frame connection using the provided
        framing.

        Args:
            framing: The framing used to encode and decode frames over
                the stream.
            logger: Optional logger used to report encoding or decoding
                errors.

        Returns:
            A frame connection that applies the specified framing over
            this stream.
        """
        return await DecodedStream.create(
            wrapping = self,
            framing = framing,
            logger = logger,
        )