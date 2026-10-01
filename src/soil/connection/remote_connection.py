from typing import override

from ..components import Distributor, Receiver
from ..data import Path, SampleTree
from ..messaging import MessageConnection
from ..requests import Request
from .remote_data_collector import RemoteDataCollector


class RemoteConnection(Receiver, Distributor):
    """
    Process data from a remote component that transmits data.

    A `RemoteConnection` is used for connections to remote components
    that transmit data without being requested, and that can also receive data.

    Messages grouped via ids are combined into a single tree before being
    handed to the registered receiver.
    """

    def __init__(self, connection: MessageConnection, batches: RemoteDataCollector):
        self._connection = connection
        """ The connection to receive messages """

        self._batches = batches
        """ The object managing active message batches """

    @classmethod
    async def create(
        cls,
        receiver: Receiver,
        connection: MessageConnection,
        batchTimeout: float = 30.0,
    ) -> 'RemoteConnection':
        """
        Create an interface to a remote transmitter.

        Args:
            receiver: The receiver to get data from the remote.
            connection: The connection to the component via a transport layer.
            batchTimeout: The number of seconds to wait for incoming data
                batches.
        """
        _batches = RemoteDataCollector(
            receiver=receiver,
            batchTimeout=batchTimeout,
        )

        self = cls(connection, _batches)

        # Register to receive messages from the component
        await connection.setReceiver(self._batches)
        return self

    @property
    def connection(self) -> MessageConnection:
        """ The connection to the remote """
        return self._connection

    # MARK: - Receiver

    @override
    def accept(self, tree: SampleTree, path: Path) -> Request:
        """
        Forward a tree to the remote component.

        Args:
            tree: The tree to send.
            path: The path of the tree.
        """
        return self._connection.accept(tree, path)

    # MARK: - Distributor

    def setReceiver(self, receiver: Receiver | None) -> Request:
        """
        Set the receiver for data received over the connection.

        Args:
            receiver: The receiver of the data coming in over this connection.
        """
        return self._batches.setReceiver(receiver)

    async def getReceiver(self) -> Receiver | None:
        """
        Get the receiver of incoming messages of this connection.
        """
        return await self._batches.getReceiver()