from abc import ABC, abstractmethod

from .receiver import Receiver


class Distributor(ABC):
    """
    A distributor represents a component that transmits data without being prompted

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
    def setReceiver(self, receiver: Receiver | None) -> None:
        """
        Set the receiver of data transmitted by the component

        Parameters
        ----------
        receiver: Receiver | None
            The receiver of the transmitted data
        """
        pass

    @abstractmethod
    def getReceiver(self) -> Receiver | None:
        """
        Get the current receiver of data transmitted by the component

        Returns
        -------
        Receiver | None
            The current receiver, if set
        """
        pass