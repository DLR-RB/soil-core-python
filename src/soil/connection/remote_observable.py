from typing import override

from ..components import Receiver, Observable
from ..data import SampleTree, Path
from ..messaging import MessageConnection, MessageReceiver, Message, MessageType
from ..requests import Request, CompletedRequest
from ..subscriptions import SubscriptionTree
from ..utils import Actor, synchronized


class RemoteObservable(Actor, MessageReceiver, Observable):
    """
    Connect to an observable component via a transport layer.
    """

    def __init__(self, connection: MessageConnection):
        Actor.__init__(self)
        self.connection = connection
        """ The connection to the remote component via the underlying transport layer """

        self._subscriptions = SubscriptionTree()
        """ The subscription tree with the inclusion and exclusion rules """

        self._receiver: Receiver | None = None
        """ The receiver of the subscription updates """

    @classmethod
    async def create(
        cls,
        connection: MessageConnection,
    ) -> 'RemoteObservable':
        """
        Create an interface to work with a remote observable component.

        Args:
            connection: The connection to the component.
        """
        self = cls(connection)

        # Register to receive messages from the component
        await connection.setReceiver(self)

        return self

    # MARK: - Transport Layer Interaction

    async def _didReceiveData(self, message: Message):
        """
        Process a data message by checking which subscription it matches.

        Args:
            message: The received data message.
        """
        # Note: We know that the message is a data message
        if self._receiver is None:
            return

        # Reduce the received tree according to the subscription rules
        reduced = self._subscriptions.reduce(message.data, message.path)
        if reduced is None:
            return

        # Note: We don't wait for subscription receiver requests
        await self._receiver.accept(reduced, message.path).wait()

    def _send(self, message: Message):
        """
        Send a message to the component.

        Args:
            message: The message to send.

        Note:
            If no message callback is available, then the message is discarded.

        Returns:
            The request to send the message.
        """
        return self.connection.send(message)

    # MARK: - Message Receiver

    @override
    @synchronized
    async def acceptMessage(self, message: Message) -> None:
        """
        Callback to receive messages from the remote component.

        Args:
            message: The message received over the connection.

        Note:
            This function is called automatically by the connection, and
            should not be called manually.
        """
        match message.type:
            case MessageType.DATA:
                await self._didReceiveData(message)

            case (
                MessageType.REQUEST
                | MessageType.DELETION
                | MessageType.SUBSCRIPTION_INCLUSION
                | MessageType.SUBSCRIPTION_DELETION
                | MessageType.SUBSCRIPTION_EXCLUSION
            ):
                pass

    # MARK: - Distributor

    @override
    def setReceiver(self, receiver: Receiver | None) -> Request:
        """
        Set the receiver for subscription data.

        Args:
            receiver: The receiver of data matching the subscription rules.
        """
        self._receiver = receiver
        return CompletedRequest()

    @override
    async def getReceiver(self) -> Receiver | None:
        """
        Get the receiver for matching data.

        Returns:
            The receiver, if set.
        """
        return self._receiver

    # MARK: - Observable

    @override
    def include(
        self,
        path: Path,
        depth: int | None = None,
    ) -> Request:
        """
        Internal function called by a subscription object to include a path in
        a subscription.

        If the subscription exists, then a request to include the path will be
        sent to the remote, and the internal subscription state will be updated.
        If no subscription exists (or was already canceled), then the function
        does nothing.
        """
        # Track the state of the subscription internally,
        # to ensure that updates are properly matched
        self._subscriptions.include(path, depth)

        return self.connection.send(
            Message.include(path, depth)
        )

    @override
    def exclude(
        self,
        path: Path,
        depth: int | None = None,
    ) -> Request:
        """
        Internal function called by a subscription object to exclude a path
        from a subscription.

        If the subscription exists, then a request to exclude the path will be
        sent to the remote, and the internal subscription state will be updated.
        If no subscription exists (or was already canceled), then the function
        does nothing.
        """
        # Track the state of the subscription internally,
        # to ensure that updates are properly matched
        self._subscriptions.exclude(path, depth)

        return self.connection.send(
            Message.exclude(path, depth)
        )

    @override
    def deleteRules(
        self,
        path: Path,
        depth: int | None = None,
    ) -> Request:
        """
        Internal function called by a subscription object to delete rules of a
        subscription.

        If the subscription exists, then a request to remove the rules will be
        sent to the remote, and the internal subscription state will be updated.
        If no subscription exists (or was already canceled), then the function
        does nothing.
        """
        # Track the state of the subscription internally,
        # to ensure that updates are properly matched
        self._subscriptions.deleteRules(path, depth)

        return self.connection.send(
            Message.deleteRules(path, depth)
        )

    @override
    async def isSubscribed(self, path: Path) -> bool:
        """
        Check if a particular path is covered by the current subscription rules.

        Args:
            path: The path to check against the subscription rules.

        Returns:
            ``True`` if the path matches.
        """
        return self._subscriptions.isSubscribed(path)

    @override
    async def reduce(self, tree: SampleTree, path: Path) -> SampleTree | None:
        """
        Use the subscription rules to remove all excluded parts of a tree.

        Args:
            tree: The original tree to strip.
            path: The path of the tree in relation to the subscription tree.

        Returns:
            The reduced tree, if any inclusion rules match, otherwise ``None``.
        """
        return self._subscriptions.reduce(tree, path)
