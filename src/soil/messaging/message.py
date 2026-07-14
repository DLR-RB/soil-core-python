from dataclasses import dataclass, field
from typing import Optional

from soil.data.sample import Sample

from ..data.immutable_tree import ImmutableSampleTree
from ..data.path import Path
from ..data.sampletree import SampleTree
from ..data.timestamp import Timestamp
from ..data.value import Value

from .message_type import MessageType


@dataclass(frozen=True)
class Message:
    """
    A message to transmit between components.

    This class implements all message types (see ``MessageType``)
    in a single message through optional fields.
    """

    type: MessageType = MessageType.DATA
    """ Indicate the message type (may be omitted for a data message) """

    path: Path = Path()
    """
    The identifying path of the data contained at the top level
    of this message.

    Usage:
    - Data message: The path associated with the sample(s)
    - Request message: The requested path
    - Subscription inclusion: The path to include
    - Subscription exclusion: The path to exclude
    - Subscription deletion: The path for which to delete
      subscription rules
    """

    data: SampleTree = field(
        default_factory=lambda: ImmutableSampleTree.empty()
    )
    """
    A data associated with the ``path``.

    Usage:
    - Data message: The tree associated with the path
    """

    count: Optional[int] = None
    """
    A generic count or limit.

    Usage:
    - Data message: Indicates the total number of messages for
      the request (if a request id is set)
    - Request message: The maximum number of samples to return
    """

    depth: Optional[int] = None
    """
    The depth of a tree.

    Usage:
    - Request message: The maximum depth
    - Subscription inclusion: The depth of the inclusion
    - Subscription exclusion: The depth of the exclusion
    """

    time: Optional[Timestamp] = None
    """
    A (start) date.

    Usage:
    - Data message: Used together with ``data`` to indicate the
      timestamp (``None`` represents the current time)
    - Request message: Used as the start date for the request
    """

    end: Optional[Timestamp] = None
    """
    The end date used in requests.

    Usage:
    - Request message: Used to indicate the end of a request interval
    """

    id: Optional[int] = None
    """
    The id of the request or subscription.

    Usage:
    - Data message: Identifies the request that this value
      corresponds to
    - Request message: An identifier to include in responses
    - Subscription message: The unique id of the subscription
    """

    @classmethod
    def acknowledge(
        cls,
        request: int,
        path: Path,
        timestamp: Timestamp | None = None,
    ) -> Message:
        """
        Create an empty acknowledgement message.

        Parameters
        ----------
        request:
            The identifier of the original request.
        path:
            The path of the original request.
        timestamp:
            Optional processing timestamp.

        Returns
        -------
        Message
            An empty data message acknowledging the request.

        Notes
        -----
        The message type is set to ``MessageType.DATA``.
        """
        return cls(
            type=MessageType.DATA,
            path=path,
            time=timestamp,
            id=request,
        )

    @classmethod
    def value(
        cls,
        value: Value,
        path: Path,
        timestamp: Timestamp | None = None,
        request: int | None = None,
        totalMessages: int | None = None,
    ) -> Message:
        """
        Create a data message containing a single value.

        Parameters
        ----------
        value:
            The value to transmit.
        path:
            The path associated with the value.
        timestamp:
            Timestamp associated with the value.
            ``None`` indicates the current time.
        request:
            Optional request identifier if this message is
            part of a response.
        totalMessages:
            Total number of messages expected in the response.

        Returns
        -------
        Message
            A data message containing a single sample.

        Notes
        -----
        The message type is set to ``MessageType.DATA``.
        """
        return cls(
            type = MessageType.DATA,
            path = path,
            data = ImmutableSampleTree.ofValue(value, timestamp),
            count = totalMessages,
            id = request,
        )

    @classmethod
    def samples(
        cls,
        samples: list[Sample],
        path: Path,
        request: int | None = None,
        totalMessages: int | None = None,
    ) -> Message:
        """
        Create a data message containing multiple samples.

        Parameters
        ----------
        samples:
            Samples to transmit.
        path:
            The path associated with the samples.
        request:
            Optional request identifier.
        totalMessages:
            Total number of messages expected in the response.

        Returns
        -------
        Message
            A data message containing multiple samples.

        Notes
        -----
        The message type is set to ``MessageType.DATA``.
        """
        return cls(
            type = MessageType.DATA,
            path = path,
            data = ImmutableSampleTree(samples=samples),
            count = totalMessages,
            id = request,
        )

    @classmethod
    def tree(
        cls,
        tree: SampleTree,
        path: Path,
        request: int | None = None,
        totalMessages: int | None = None,
    ) -> Message:
        """
        Create a data message containing a sample tree.

        Parameters
        ----------
        tree:
            The sample tree to transmit.
        path:
            The path associated with the tree.
        request:
            Optional request identifier.
        totalMessages:
            Total number of messages expected in the response.

        Returns
        -------
        Message
            A data message containing a tree.

        Notes
        -----
        The message type is set to ``MessageType.DATA``.
        """
        return cls(
            type = MessageType.DATA,
            path = path,
            data = tree,
            count = totalMessages,
            id = request,
        )

    @classmethod
    def request(
        cls,
        path: Path,
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        limit: int | None = None,
        depth: int | None = None,
        id: int | None = None,
    ) -> Message:
        """
        Create a history request.

        Parameters
        ----------
        path:
            The path for which history is requested.
        start:
            Exclusive start date.
            ``None`` indicates the beginning of time.
        end:
            Inclusive end date.
            ``None`` indicates the end of time.
        limit:
            Maximum number of samples to return.
        depth:
            Number of levels below the path to include.
        id:
            Optional request identifier.

        Returns
        -------
        Message
            A history request message.

        Notes
        -----
        The message type is set to ``MessageType.REQUEST``.
        """
        return cls(
            type = MessageType.REQUEST,
            path = path,
            time = start,
            count = limit,
            depth = depth,
            end = end,
            id = id,
        )

    @classmethod
    def delete(
        cls,
        path: Path,
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
        id: int | None = None,
    ) -> Message:
        """
        Create a deletion request.

        Parameters
        ----------
        path:
            The path for which deletion is requested.
        start:
            Exclusive start date.
            ``None`` indicates the beginning of time.
        end:
            Inclusive end date.
            ``None`` indicates the end of time.
        depth:
            Number of levels below the path to delete.
        id:
            Optional request identifier.

        Returns
        -------
        Message
            A deletion request message.

        Notes
        -----
        The message type is set to
        ``MessageType.DELETION``.
        """
        return cls(
            type = MessageType.DELETION,
            path = path,
            time = start,
            depth = depth,
            end = end,
            id = id,
        )

    @classmethod
    def include(
        cls,
        path: Path,
        subscription: int,
        depth: int | None = None,
    ) -> Message:
        """
        Create a subscription inclusion request.

        Parameters
        ----------
        path:
            The path to subscribe to.
        subscription:
            Subscription identifier.
        depth:
            Number of levels below the path to include.

        Returns
        -------
        Message
            A subscription inclusion request.

        Notes
        -----
        The message type is set to
        ``MessageType.SUBSCRIPTION_INCLUSION``.
        """
        return cls.subscriptionRequest(
            MessageType.SUBSCRIPTION_INCLUSION,
            subscription,
            path,
            depth,
        )

    @classmethod
    def exclude(
        cls,
        path: Path,
        subscription: int,
        depth: int | None = None,
    ) -> Message:
        """
        Create a subscription exclusion request.

        Parameters
        ----------
        path:
            The path to exclude.
        subscription:
            Subscription identifier.
        depth:
            Number of levels below the path to exclude.

        Returns
        -------
        Message
            A subscription exclusion request.

        Notes
        -----
        The message type is set to
        ``MessageType.SUBSCRIPTION_EXCLUSION``.
        """
        return cls.subscriptionRequest(
            MessageType.SUBSCRIPTION_EXCLUSION,
            subscription,
            path,
            depth,
        )

    @classmethod
    def deleteRules(
        cls,
        path: Path,
        subscription: int,
        depth: int | None = None,
    ) -> Message:
        """
        Create a subscription rule deletion request.

        Parameters
        ----------
        path:
            Path for which subscription rules should be removed.
        subscription:
            Subscription identifier.
        depth:
            Number of levels below the path affected.

        Returns
        -------
        Message
            A subscription deletion request.

        Notes
        -----
        The message type is set to
        ``MessageType.SUBSCRIPTION_DELETION``.
        """
        return cls.subscriptionRequest(
            MessageType.SUBSCRIPTION_DELETION,
            subscription,
            path,
            depth,
        )

    @classmethod
    def subscriptionRequest(
        cls,
        messageType: MessageType,
        subscription: int,
        path: Path,
        depth: int | None = None,
    ) -> Message:
        """
        Create a subscription modification request.

        Parameters
        ----------
        messageType:
            The subscription operation type.
        subscription:
            Subscription identifier.
        path:
            Path to modify.
        depth:
            Number of levels below the path affected.

        Returns
        -------
        Message
            A subscription operation message.

        Notes
        -----
        This method is used internally by
        ``include()``, ``exclude()``, and
        ``delete_rules()``.
        """
        return cls(
            type = messageType,
            path = path,
            depth = depth,
            id = subscription,
        )

    def __str__(self) -> str:
        """
        Return a human-readable representation of the message.

        Returns
        -------
        str
            A multiline description of the message and its content.
        """
        content = [f"type: {self.type}"]

        if self.path.isEmpty:
            content.append(f"path: {self.path}")

        if self.count is not None:
            content.append(f"count: {self.count}")

        if self.depth is not None:
            content.append(f"depth: {self.depth}")

        if self.id is not None:
            content.append(f"id: {self.id}")

        if self.time is not None:
            content.append(f"time: {self.time}")

        if self.end is not None:
            content.append(f"end: {self.end}")

        if not self.data.isEmpty:
            content.append("data:")
            content.extend(
                self.data.describe(indentLevel=1)
            )

        return "\n".join(content)

    def __eq__(self, other: object) -> bool:
        """
        Compare two messages for equality.

        Timestamp fields are compared with a tolerance of
        1 millisecond to match the Swift implementation.
        """
        if not isinstance(other, Message):
            return NotImplemented

        return (
            self.type == other.type
            and self.path == other.path
            and self.count == other.count
            and self.depth == other.depth
            and self.id == other.id
            and _compareTimestamp(self.time, other.time)
            and _compareTimestamp(self.end, other.end)
            and self.data.isEqualTo(other.data)
        )


def _compareTimestamp(
    timestamp: Timestamp | None,
    other: Timestamp | None,
) -> bool:
    """
    Compare two timestamps with a tolerance.

    Parameters
    ----------
    timestamp:
        First timestamp.
    other:
        Second timestamp.

    Returns
    -------
    bool
        True if the timestamps are effectively equal.
    """
    if timestamp is None:
        return other is None

    if other is None:
        return False

    return abs(timestamp - other).seconds < 0.001