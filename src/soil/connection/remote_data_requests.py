
from ..messaging import Message
from .data_request import DataRequest


class RemoteDataRequests:
    """
    Handle active requests to a remote storage component.
    """

    def __init__(self):
        """
        Create a handler to manage requests.
        """

        #: The currently active requests, indexed by their id
        self._activeRequests: dict[int, DataRequest] = {}

        # MARK: - Ids

        """
        The id used for the most recent request.

        This id is always incremented for the next request,
        so that the first request of the component has id ``1``.
        """
        self.lastRequestId = 0

    # MARK: - Ids

    def nextId(self) -> int:
        """
        Get the next request id for the component.

        The request id is incremented from 1,
        while a connection to the component is active.
        """
        self.lastRequestId += 1
        return self.lastRequestId

    # MARK: - Requests

    def add(self, request: DataRequest, id: int):
        """
        Add an active request.

        Args:
            request: The new request.
            id: The unique request id.

        Note:
            An existing request for the id will be canceled.
        """
        previous = self._activeRequests.get(id)
        if previous is not None:
            previous.finish()

        # Note: Timeout for requests are handled by the caller.
        # Each request includes a timeout task, which will be canceled
        # when the request is completed.
        # If a timeout is reached, then `cancelRequest()` will be called
        # by the caller.
        self._activeRequests[id] = request

    def didReceive(self, response: Message) -> bool:
        """
        Process a received message and update a matching request.

        Args:
            response: The message to process.

        Returns:
            ``True`` if a matching request was updated.
        """
        if response.id is None:
            # No request id, so we ignore the message
            return False

        request = self._activeRequests.get(response.id)
        if request is None:
            # No active request, so we ignore the message
            return False

        request.update(response)

        # Remove request if completed
        if request.hasReceivedAllExpectedMessages:
            self._activeRequests.pop(response.id, None)
            request.finish()

        return True

    def cancelRequest(self, id: int) -> bool:
        """
        Cancel an active request.

        Args:
            id: The id of the request to cancel.

        Returns:
            ``True`` if the request was found and canceled.
        """
        request = self._activeRequests.get(id)
        if request is None:
            # No active request, so we ignore the timeout
            return False

        self._activeRequests.pop(id, None)
        request.finish()
        return True

    @property
    def numberOfRequests(self) -> int:
        """
        The number of currently active requests.
        """
        return len(self._activeRequests)

    def hasRequest(self, id: int) -> bool:
        """
        Indicate if a request with the given id is active.

        Args:
            id: The id of the request.

        Returns:
            ``True`` if a request with the id is active.
        """
        return id in self._activeRequests
