from abc import ABC, abstractmethod

from ..requests import Request

from .receiver import MessageReceiver


class MessageDistributor(ABC):
    """
    A message distributor represents a component that transmits message without being prompted
    """

    @abstractmethod
    def setReceiver(self, receiver: MessageReceiver | None) -> Request:
        """
        Set the receiver of messages transmitted by the component

        Parameters
        ----------
        receiver: Receiver | None
            The receiver of the transmitted messages

        Returns
        -------
        Request
            The request to optionally wait for until the receiver is set
        """
        pass

    @abstractmethod
    async def getReceiver(self) -> MessageReceiver | None:
        """
        Get the current receiver of messages transmitted by the component

        Returns
        -------
        Receiver | None
            The current receiver, if set
        """
        pass