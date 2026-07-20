from abc import ABC, abstractmethod

from ..requests import Request

from .message import Message


class MessageReceiver(ABC):
    """
    A type that can receive messages.
    """

    @abstractmethod
    def acceptMessage(self, message: Message) -> Request:
        """
        Process a received message.

        Parameters:
            message (Message):
                The message to receive
        """
        pass
