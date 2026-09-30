from abc import ABC, abstractmethod

from ..requests import Request
from .receiver import FrameReceiver


class FrameDistributor(ABC):
    """
    A frame distributor represents a component that transmits frames without being prompted

    The name "distributor" was choosen to emphasize that the component is sending data
    that is not necessarily requested (in contrast to a `provider` or an `observable`).
    A `distributor` is not necessarily the source of the data it sends.
    Rejected terms:
    - transmitter: closest alternative name
    - (data) source: Not necessarily creator of data, could be a relay.
    - producer: Not necessarily creator of data, could be a relay.
    - publisher: Does not necessarily handle subscriptions.
    - dispatcher: suggests complex logic
    - notifier: suggests subscriptions
    - feed: implies continuity
    """

    @abstractmethod
    def setReceiver(self, receiver: FrameReceiver | None) -> Request:
        """
        Set the receiver of frames transmitted by the component

        Parameters
        ----------
        receiver: Receiver | None
            The receiver of the transmitted frames

        Returns
        -------
        Request
            The request to optionally wait for until the receiver is set
        """

    @abstractmethod
    async def getReceiver(self) -> FrameReceiver | None:
        """
        Get the current receiver of frames transmitted by the component

        Returns
        -------
        Receiver | None
            The current receiver, if set
        """
