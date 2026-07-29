from abc import abstractmethod

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..encoding.encoding import MessageEncoding
    from ..messaging.connection import MessageConnection

from ..logging import Logger
from ..requests import Request
from ..components import Connection

from .distributor import FrameDistributor


class FrameConnection(Connection, FrameDistributor):
    """
    A connector to a component that transmits and receives encoded messages.

    This interface defines the methods for bidirectional communication
    using encoded byte messages.
    """

    @abstractmethod
    def send(self, message: bytes) -> Request:
        """
        Send a message to the component via the underlying transport layer.

        Parameters:
            message (bytes):
                The message to send

        Returns:
            Awaitable[None]:
                An awaitable representing the transmission request.
                Note: Does not guarantee delivery, only that the message was transmitted.
        """
        pass

    async def apply(self, encoding: 'MessageEncoding', logger: Logger | None = None) -> 'MessageConnection':
        """
        Convert this connector to a message connection using the provided encoding.

        Parameters:
            encoding (MessageEncoding):
                The encoding to use for messages over the connector

        Returns:
            MessageConnection:
                The message-based connection
        """
        from ..messaging.decoded import DecodedConnection
        return await DecodedConnection.create(self, encoding, logger)
