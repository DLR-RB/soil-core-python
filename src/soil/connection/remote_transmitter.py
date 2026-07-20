from typing import override

from ..components import Distributor, Receiver
from ..messaging import MessageConnection
from ..requests import Request

from .remote_data_collector import RemoteDataCollector


class RemoteTransmitter(Distributor):
    """
    Process data from a remote component that transmits data.
    """

    def __init__(
        self,
        connection: MessageConnection,
        batches: RemoteDataCollector,
    ):
        """
        Create an interface to a remote transmitter.

        Parameters
        ----------
        connection: MessageConnection
            The connection to the component via a transport layer.
        batchTimeout: float
            The number of seconds to wait for incoming data batches
        """
        # The connection to receive messages
        self.connection = connection

        # The object managing active message batches
        self._batches = batches

    @classmethod
    async def create(
        cls,
        receiver: Receiver,
        connection: MessageConnection,
        batchTimeout: float = 30.0,
    ) -> 'RemoteTransmitter':
        """
        Create an interface to a remote transmitter.

        Parameters
        ----------
        receiver: Receiver
            The receiver to get data from the remote
        connection: MessageConnection
            The connection to the component via a transport layer.
        batchTimeout: float
            The number of seconds to wait for incoming data batches
        """
        batches = RemoteDataCollector(
            receiver=receiver,
            batchTimeout=batchTimeout,
        )

        instance = cls(
            connection=connection,
            batches=batches,
        )

        # Register to receive messages from the component
        await connection.setReceiver(batches)
        return instance


    @override
    def setReceiver(self, receiver: Receiver | None) -> Request:
        """
        Set the receiver for data received over the connection.

        Parameters
        ----------
        receiver: Receiver | None
            The receiver of the data coming in over this connection.
        """
        return self._batches.setReceiver(receiver)


    @override
    async def getReceiver(self) -> Receiver | None:
        """
        Get the receiver of incoming messages of this connection.
        """
        return await self._batches.getReceiver()
