from typing import Callable
from asyncio import Task

from ..data import MutableSampleTree, Path, SampleTree
from ..messaging import Message


class IncompleteReceivedTree:
    """
    A request for data that is not completed.
    """

    def __init__(
        self,
        timeout: Task[None],
        onComplete: Callable[[SampleTree, Path], None],
    ):
        """
        Create a request for tracking.
        """

        """
        The tree containing the received samples while waiting for more
        responses.

        Note:
            The tree is constructed for the root path.
        """
        self._tree = MutableSampleTree()

        #: The receiver to forward the tree to on completion
        self.onComplete = onComplete

        #: The timeout task to cancel if the batch is completed before timing out
        self._timeout = timeout

        #: The expected number of response messages, extracted from received responses
        self.expectedMessages: int | None = None

        #: The number of already received messages for this batch
        self.receivedMessages = 0

    def finish(self):
        """
        Complete the request.

        This function is called regardless if the request is completed or a
        timeout is reached. The timeout task will be canceled (may already be
        completed), and the completion callback is invoked with the available
        data.
        """
        self._timeout.cancel()

        # Here we need get the tree for the correct path,
        # not the tree at the root
        path, tree = self._tree.containedTree()
        self.onComplete(tree, path)

    def update(self, response: Message):
        """
        Update the active request, run the callback, and check if the request
        is completed.

        Note:
            This function expects that:
            - the message is a data message
            - the component id matches the sender of the message
            - the request id matches this request.
        """
        self._updateExpectedMessageCount(response.count)
        self.receivedMessages += 1

        self._tree.mergeAtPath(response.data, response.path)

    def _updateExpectedMessageCount(self, count: int | None):
        """
        Update the number of expected messages if the response contains this
        info.

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

        # The previous count does not match the received one, which is an
        # application error. The count should always be the same for one
        # request.
        #
        # We just use the higher value, since the component may have "found"
        # additional messages to send.
        #
        # TODO: Propagate warning about count mismatch
        if count > self.expectedMessages:
            self.expectedMessages = count

    @property
    def hasReceivedAllExpectedMessages(self) -> bool:
        """
        Indicate if the request is completed.

        The request is assumed completed if the number of received messages
        matches the stated number in the messages.
        """
        return self.receivedMessages == self.expectedMessages
