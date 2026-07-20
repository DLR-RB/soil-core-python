from abc import abstractmethod
from typing import override

from ..components.receiver import Receiver
from ..data.path import Path
from ..data.sampletree import SampleTree
from ..requests.request import Request
from ..transport.connection import Connection

from .distributor import MessageDistributor
from .message import Message


class MessageConnection(Receiver, MessageDistributor, Connection):
    """
    A connection to a component via a transport layer
    """

    @abstractmethod
    def send(self, message: Message) -> Request:
        """
        Send a message to the component via the underlying transport layer.

        Parameters:
            message (Message):
                The message to send

        Returns:
            Message:
                The transmission request, which can be awaited to wait for transmission.

        Note:
            The returned request does not wait for message delivery, only transmission.
        """
        pass

    # MARK: Receiver

    @override
    def accept(self, tree: SampleTree, path: Path = Path()) -> Request:
        """
        Send samples over the connection.

        Parameters:
            tree (SampleTree):
                The samples to send for the path.
            path (Path):
                The path associated with the samples
        Returns:
            Request:
                A request handle, to optionally wait until the data is transmitted.

        Note: This function is not marked `async`, because it is viewed as a request to send data.
        The data does not actually need to be sent when the function returns, and should return as fast as possible.
        To wait until the receive is completed, await the returned request.
        """
        return self.send(Message.tree(tree, path))
