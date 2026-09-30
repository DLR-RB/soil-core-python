from asyncio import CancelledError, Task, create_task, get_running_loop, sleep
from typing import override

from ..components import Storage
from ..data import Path, SampleTree, Timestamp
from ..messaging import Message, MessageConnection, MessageReceiver, MessageType
from ..requests import AsyncRequest, CompletedRequest, Request
from .data_request import DataRequest
from .remote_data_requests import RemoteDataRequests


class RemoteStorage(MessageReceiver, Storage):

    """
    Encapsulate a remote component that provides storage to treat it like a local storage.

    Connect to a remote storage.

    :param connection: The connection to the storage.
    :param requestTimeout: The number of seconds to wait for each request
    """
    def __init__(
        self,
        connection: MessageConnection,
        requests: RemoteDataRequests,
        requestTimeout: float = 30.0,
    ):
        # The connection to the remote
        self.connection = connection

        # The object managing active requests
        self._requests = requests

        # The number of seconds until a request times out
        self._requestTimeout = requestTimeout

    @classmethod
    async def create(
        cls,
        connection: MessageConnection,
        requestTimeout: float = 30.0,
    ) -> 'RemoteStorage':
        requests = RemoteDataRequests()
        instance = cls(
            connection=connection,
            requests=requests,
            requestTimeout=requestTimeout,
        )

        # Register to receive messages from the component
        await connection.setReceiver(instance).wait()

        return instance

    """
    Send a message to the component.

    :param message: The message to send.
    :note: If no message callback is available, then the message is discarded.
    :returns: The request to send the message
    """
    def _send(self, message: Message) -> Request:
        return self.connection.send(message=message)

    """
    Create a task that times out after a given interval.

    :param seconds: The number of seconds to wait before the timeout function is called.
    :param requestId: The id of the request that timed out
    :note: The `reachedTimeout()` function is called with the provided id when the
           task reaches its timeout
    """
    def _startRequestTimeout(
        self,
        seconds: float,
        requestId: int,
    ) -> Task[None]:

        async def timeout():
            try:
                await sleep(seconds)
                await self._reachedTimeout(requestId)
            except CancelledError:
                pass

        return create_task(timeout())

    """
    Callback function executed when a timeout for a request is reached.

    :param requestId: The request that timed out
    """
    async def _reachedTimeout(self, requestId: int):
        self._requests.cancelRequest(requestId)

    """
    Actor-isolated function to get a tree from the remote storage.

    Sends a data request, and waits for all responses.
    All samples are returned when the request completes or times out.
    """
    async def _tree(
        self,
        path: Path,
        start: Timestamp | None,
        end: Timestamp | None,
        depth: int | None,
        limit: int | None,
    ) -> SampleTree:
        requestId = self._requests.nextId()

        # Send the request message to the remote
        # If it's not delivered, then the timeout will be triggered
        self._send(
            Message.request(
                path,
                start=start,
                end=end,
                limit=limit,
                depth=depth,
                id=requestId,
            )
        )

        timeoutTask = self._startRequestTimeout(
            seconds=self._requestTimeout,
            requestId=requestId,
        )

        # Store the request and wait for the data (with a timeout)
        loop = get_running_loop()
        future = loop.create_future()

        request = DataRequest(
            path=path,
            start=start,
            end=end,
            depth=depth,
            limit=limit,
            continuation=future,
            timeout=timeoutTask,
        )

        self._requests.add(request, requestId)

        return await future

    # MARK: Message receiver

    """
    Callback to receive messages from the remote component.

    :param message: The message received over the connection
    :note: This function is called automatically by the connection, and should
           not be called manually.
    """
    @override
    def acceptMessage(self, message: Message) -> Request:
        if message.type == MessageType.DATA:
            return AsyncRequest(self._didReceive(message)
)

        if message.type in (
            MessageType.REQUEST,
            MessageType.DELETION,
            MessageType.SUBSCRIPTION_INCLUSION,
            MessageType.SUBSCRIPTION_DELETION,
            MessageType.SUBSCRIPTION_EXCLUSION,
        ):
            return CompletedRequest()

        raise ValueError(f"Unsupported message type: {message.type}")

    async def _didReceive(self, data: Message):
        self._requests.didReceive(data)

    # MARK: Storage

    """
    Receive a tree for a path.

    This is the singular function to inject data into a component.

    The provided tree can contain multiple values for each node, and be of arbitrary depth.

    Components may choose to ignore parts of the tree due to access rights or other reasons.

    :param tree: The tree to store.
    :param path: The path of the root node of the provided tree
    :note: This function is not async, because it is viewed as a request to store data.
           The data does not actually need to be stored when the function returns,
           and should return as fast as possible.
    """
    @override
    def accept(self, tree: SampleTree, path: Path) -> Request:
        return self.connection.accept(tree, path)

    """
    Read a data tree for a given path within a given interval.

    This is the singular function to serve all data retrieval needs.

    The sort order of the result is:
    - ascending, if `end = None`
    - descending, if `end != None` and `start = None`
    - ascending, if `start < end`
    - descending, if `start > end`

    The `limitPerNode` is applied in sort order.

    :param path: The requested path.
    :param start: The start of the requested interval (exclusive, defaults to None,
                  meaning from beginning of time)
    :param end: The end of the requested interval (inclusive, defaults to None,
                meaning to end of time)
    :param depth: The number of levels below the path to include in the result
    :param limitPerNode: The maximum number of values to return for each node of
                         the tree (defaults to None, i.e. no limit)
    :returns: The tree with the given depth, limited to the maximum count per
              node, for the requested interval.
    :note: This function is async because providing the data may take some time.
           It could be retrieved over a network, from an otherwise slow database,
           or from other components.
    """
    @override
    async def tree(
        self,
        path: Path,
        start: Timestamp | None,
        end: Timestamp | None,
        depth: int | None,
        limitPerNode: int | None,
    ) -> SampleTree:
        return await self._tree(
            path=path,
            start=start,
            end=end,
            depth=depth,
            limit=limitPerNode,
        )

    """
    Delete data from the storage.

    :param path: The path of the node targeted for the delete.
    :param start: The start of the interval to delete (exclusive, defaults to None,
                  meaning from beginning of time)
    :param end: The end of the interval to delete (inclusive, defaults to None,
                meaning to end of time)
    :param depth: The number of levels to include for deletion below the given path
    """
    @override
    def delete(
        self,
        path: Path = Path(),
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
    ) -> Request:
        # TODO: Track deletion requests
        message = Message.delete(
            path,
            start=start,
            end=end,
            depth=depth,
            id=None,
        )
        return self.connection.send(message=message)
