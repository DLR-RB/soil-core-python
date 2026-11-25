"""
Example: Observable Component

Demonstrates the Observable pattern: a component that tracks subscriptions
and only forwards the parts of a data tree that a receiver is subscribed to.

This example implements a small in-memory `Observable` directly, to make the
subscribed/not-subscribed distinction visible. In your own code you can reuse
the built-in `ObservingStorage`, which provides an observable storage on top of
this same interface.
"""

import asyncio

from soil.components import Observable, Receiver
from soil.data import Path, SampleTree, Value
from soil.messaging import Message, MessageType
from soil.requests import CompletedRequest, Request


class DataObservable(Observable):
    """An in-memory observable that forwards only matching data."""

    def __init__(self) -> None:
        self._receiver: Receiver | None = None
        self._data: SampleTree = SampleTree()
        self._inclusions: list[Path] = []

    # MARK: - Subscription rules

    def include(self, path: Path, depth: int | None) -> Request:
        self._inclusions.append(path)
        return CompletedRequest()

    def exclude(self, path: Path, depth: int | None) -> Request:
        self._inclusions = [
            item for item in self._inclusions if not item.hasPrefix(path)
        ]
        return CompletedRequest()

    def deleteRules(self, path: Path, depth: int | None) -> Request:
        self._inclusions = [
            item for item in self._inclusions if not item.hasPrefix(path)
        ]
        return CompletedRequest()

    async def isSubscribed(self, path: Path) -> bool:
        # A path is covered when it sits at or below an included path,
        # or when the root is included.
        return any(
            includePath.isEmpty or path.hasPrefix(includePath)
            for includePath in self._inclusions
        )

    async def reduce(self, tree: SampleTree, path: Path) -> SampleTree | None:
        return tree if await self.isSubscribed(path) else None

    # MARK: - Distributor

    async def setReceiver(self, receiver: Receiver | None) -> Request:
        self._receiver = receiver
        return CompletedRequest()

    async def getReceiver(self) -> Receiver | None:
        return self._receiver

    # MARK: - Data

    async def acceptMessage(self, message: Message) -> None:
        """Store incoming data and forward it to the current receiver."""
        if message.type == MessageType.DATA:
            self._data.mergeAtPath(message.data, message.path)
            await self.distribute(
                self._data.existingNode(message.path) or SampleTree(),
                message.path,
            )


class UpdateCollector(Receiver):
    """A receiver that prints the values it receives."""

    def accept(self, tree: SampleTree, path: Path = Path()) -> Request:
        sample = tree.newestSample
        if sample is not None:
            print(f"Received update at {path}: {sample.value.value}")
        return CompletedRequest()


async def main():
    observable = DataObservable()
    collector = UpdateCollector()
    await observable.setReceiver(collector)

    # Subscribe to everything below `sensor > temperature` only.
    await observable.include(Path.of("sensor", "temperature"), depth=2)

    # This value matches the subscription and reaches the collector.
    await observable.acceptMessage(
        Message.value(Value(21.5), Path.of("sensor", "temperature"))
    )

    # This value does not match and is filtered out.
    await observable.acceptMessage(
        Message.value(Value(63), Path.of("sensor", "humidity"))
    )


if __name__ == "__main__":
    asyncio.run(main())
