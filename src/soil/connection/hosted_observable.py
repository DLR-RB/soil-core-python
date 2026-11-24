from typing import override

from ..components import Observable, Receiver
from ..data import Path, SampleTree
from ..messaging import Message, MessageConnection, MessageReceiver, MessageType
from ..requests import CompletedRequest, Request


class HostedObservable(MessageReceiver, Receiver):
    """
    Provides access to an observable through a transport interface.
    """

    def __init__(self, observable: Observable, connection: MessageConnection):
        """
        Create hosting for an observable over a connection.

        Args:
            observable: The component to expose.
            connection: The connection to use for hosting.
        """
        #: The observed component that is exposed
        self._observable = observable

        #: The connection over which the observable is exposed
        self.connection = connection

    @classmethod
    async def create(cls, observable: Observable, connection: MessageConnection) -> 'HostedObservable':
        self = cls(observable, connection)
        await connection.setReceiver(self)
        await observable.setReceiver(self)
        return self

    # MARK: - Subscription Message Handling

    def _didReceiveSubscriptionRequest(self, request: Message) -> Request:
        """
        Process subscription messages received over the connection.

        Args:
            request: The received subscription request message.
        """
        match request.type:
            case MessageType.SUBSCRIPTION_INCLUSION:
                return self._observable.include(request.path, depth=request.depth)

            case MessageType.SUBSCRIPTION_DELETION:
                return self._observable.deleteRules(request.path, depth=request.depth)

            case MessageType.SUBSCRIPTION_EXCLUSION:
                return self._observable.exclude(request.path, depth=request.depth)

            case _:
                 # Non-subscription requests handled elsewhere
                return CompletedRequest()

    # MARK: Subscription control

    @override
    def include(
        self,
        path: Path,
        depth: int | None,
    ) -> Request:
        """
        Include a path in the subscription.

        Args:
            path: The path to include.
            depth: The depth of the inclusion (``None`` indicates the full
                sub-tree).

        Returns:
            A request to wait for completion of the inclusion.
        """
        return self._observable.include(path, depth=depth)

    @override
    def exclude(
        self,
        path: Path,
        depth: int | None,
    ) -> Request:
        """
        Exclude a path from the subscription.

        Args:
            path: The path to exclude.
            depth: The depth of the exclusion (``None`` indicates the full
                sub-tree).

        Returns:
            A request to wait for completion of the exclusion.
        """
        return self._observable.exclude(path, depth=depth)

    @override
    def deleteRules(
        self,
        path: Path,
        depth: int | None,
    ) -> Request:
        """
        Delete subscription rules at a path with a given depth.

        Args:
            path: The path for which to delete rules.
            depth: The depth of the deletion.

        Returns:
            A request to wait for completion of the deletion.
        """
        return self._observable.deleteRules(path, depth=depth)

    @override
    async def isSubscribed(
        self,
        path: Path,
    ) -> bool:
        """
        Check if a path is covered by the subscription rules.

        Args:
            path: The path to check.

        Returns:
            ``True`` if the path is subscribed.
        """
        return await self._observable.isSubscribed(path)

    @override
    async def reduce(
        self,
        tree: SampleTree,
        path: Path,
    ) -> SampleTree | None:
        """
        Use the subscription rules to remove all excluded parts of a tree.

        Args:
            tree: The original tree to strip.
            path: The path of the tree in relation to the subscription tree.

        Returns:
            The reduced tree, if any inclusion rule matches, otherwise ``None``.
        """
        return await self._observable.reduce(tree, path)

    # MARK: - Message Receiver

    @override
    def acceptMessage(self, message: Message) -> Request:
        """
        Insertion point for messages received over the connection.

        Only subscription messages are considered when hosting observable
        components.

        Args:
            message: The message received over the connection.

        Note:
            This function is called automatically by the connection, and should
            not be called manually.
        """
        match message.type:
            case (
                MessageType.DATA
                | MessageType.REQUEST
                | MessageType.DELETION
            ):
                return CompletedRequest()

            case (
                MessageType.SUBSCRIPTION_INCLUSION
                | MessageType.SUBSCRIPTION_DELETION
                | MessageType.SUBSCRIPTION_EXCLUSION
            ):
                return self._didReceiveSubscriptionRequest(message)

    # MARK: - Receiver

    @override
    def accept(self, tree: SampleTree, path: Path) -> Request:
        """
        Receive updates matching the subscriptions from the wrapped observable
        to send over the connection.

        Note:
            This function is called automatically by the wrapped observable.
            It should not be called manually.
        """
        return self.connection.accept(tree, path)
