from abc import ABC, abstractmethod

from .message import Message


class MessageReceiver(ABC):
    """
    A type that can receive messages.
    """

    @abstractmethod
    async def didReceive(self, message: Message):
        """
        Process a received message.

        Parameters:
            message (Message):
                The message to receive
        """
        pass
