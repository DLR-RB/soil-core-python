from asyncio import Future, Task

from ..data import (
    ImmutableSampleTree,
    MutableSampleTree,
    Path,
    Sample,
    SampleTree,
    Timestamp,
)
from ..messaging import Message


class DataRequest:
    """
    A request for data that is not completed
    """

    def __init__(
        self,
        path: Path,
        start: Timestamp | None,
        end: Timestamp | None,
        depth: int | None,
        limit: int | None,
        continuation: Future[SampleTree],
        timeout: Task[None],
    ):
        """
        Create a request for tracking
        """

        #: The path contained in the request
        self.path = path

        #: The (start) time of the requested interval
        self.start = start

        #: The end time of the requested interval
        self.end = end

        #: The requested depth of the data to provide
        self.depth = depth

        #: The maximum number of samples per node
        self.limit = limit

        """
        The tree containing the received samples while waiting for more responses

        Note:
            The tree is constructed for the root path.
        """
        self._tree = MutableSampleTree()

        #: The continuation to execute when the request is completed or timed out
        self.continuation = continuation

        #: The timeout task to cancel if the request is completed before timing out
        self._timeout = timeout

        #: The expected number of response messages, extracted from received responses
        self.expectedMessages: int | None = None

        #: The number of already received messages for this request
        self.receivedMessages = 0

    def finish(self):
        """
        Complete the request.

        This function is called regardless if the request is completed or a timeout
        is reached. The timeout task will be canceled (may already be completed),
        and the continuation is resumed with the available data.
        """
        self._timeout.cancel()

        # Here we need get the tree for the correct path,
        # not the tree at the root
        node = self._tree.existingNode(self.path)
        tree = node.tree() if node is not None else ImmutableSampleTree()

        self.continuation.set_result(tree)

    def _matches(self, path: Path) -> bool:
        """
        Check that the path in the response matches the request.

        For all requests the response must either:
        - Match perfectly for inclusions, exclusions and history requests
        - Be a sub-path of the request for value requests within the requested depth
        """

        # All responses for a value request must be in the requested sub-tree
        if not path.hasPrefix(self.path):
            return False

        if self.depth is None:
            # Without a depth, the only requirement is to be within the sub-tree
            return True

        # With a depth, the remaining path must not be too long
        remainingDepth = len(path) - len(self.path)
        return remainingDepth <= self.depth

    def update(self, response: Message) -> bool:
        """
        Update the active request, run the callback, and check if the request is completed.

        Note:
            This function expects that:
            - the message is a data message
            - the component id matches the sender of the message
            - the request id matches this request.

        Returns:
            ``True`` if the request matched and was processed.
        """

        if not self._matches(response.path):
            # TODO: Should we still update the expected message count if the path is incorrect?
            # The misbehaving client may include this message in the count,
            # which would cause the request to not be completed.

            # Note: We could also end up here if a malicious client attempts to use a request
            # to respond with unrelated data that it's not allowed to write, in an attempt
            # to circumvent access restrictions
            return False

        self._updateExpectedMessageCount(response.count)
        self.receivedMessages += 1

        # Insert the data into the tree
        # TODO: Limit the number of samples, and the date interval
        self._tree.mergeAtPath(response.data, response.path)

        return True

    def _limit(self, samples: list[Sample]) -> list[Sample]:
        """
        Restrict the samples to the requested interval
        """

        if self.start is None:
            if self.end is None:
                # No interval given, so all samples are relevant
                return samples

            # Only end given, so remove all after end (end is inclusive)
            return [sample for sample in samples if sample.time <= self.end]

        if self.end is None:
            # Only start given, so remove all before start (start is exclusive)
            return [sample for sample in samples if sample.time > self.start]

        if self.start >= self.end:
            # Reverse order (start is exclusive, end is inclusive)
            return [
                sample
                for sample in samples
                if sample.time < self.start and sample.time >= self.end
            ]

        # "Normal" order (start is exclusive, end is inclusive)
        return [
            sample
            for sample in samples
            if sample.time > self.start and sample.time <= self.end
        ]

    def _updateExpectedMessageCount(self, count: int | None):
        """
        Update the number of expected messages if the response contains this info.

        Note:
            If a mismatching count is received, then the larger one is used.
        """

        if count is None:
            # Keep the existing count, since no new one received
            return

        if self.expectedMessages is None:
            # No previous count, so set the received one
            self.expectedMessages = count
            return

        if count == self.expectedMessages:
            return

        # The previous count does not match the received one, which is an application error.
        # The count should always be the same for one request.
        # We just use the higher value, since the component may have "found"
        # additional messages to send.
        # TODO: Propagate warning about count mismatch
        self.expectedMessages = max(self.expectedMessages, count)

    @property
    def hasReceivedAllExpectedMessages(self) -> bool:
        """
        Indicate if the request is completed.

        The request is assumed completed if the number of received messages
        matches the stated number in the messages.
        """
        return self.receivedMessages == self.expectedMessages