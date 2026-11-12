"""
Example: Storage Component

Demonstrates how to use the Storage component to store, retrieve, and delete data.
"""

import asyncio

from soil.data import Path, SampleTree, Timestamp, Value
from soil.components import Storage, Provider, Receiver
from soil.messaging import Message, MessageType


class InMemoryStorage(Storage):
    """A simple in-memory storage implementing the Storage interface."""

    def __init__(self):
        self._data: SampleTree = SampleTree()
        self._receiver: Receiver | None = None

    # MARK: - Provider Interface (Read)

    async def tree(
        self,
        path: Path,
        start: Timestamp | None,
        end: Timestamp | None,
        depth: int | None,
        limitPerNode: int | None
    ) -> SampleTree:
        """Read a data tree for a given path within a given interval."""
        node = self._data.existingNode(path)
        if node is None:
            return SampleTree()

        # Get samples in the requested interval
        samples = node.getSamples(start, end, limitPerNode)

        # Build result tree
        result = SampleTree.ofSamples(samples, path)

        # Include children up to the requested depth
        if depth is None or depth > 0:
            for childName, child in node.children.items():
                childPath = path.appending(childName)
                childTree = await self.tree(childPath, start, end,
                                          depth - 1 if depth else None,
                                          limitPerNode)
                result.merge(childTree)

        return result

    # MARK: - Receiver Interface (Write)

    async def acceptMessage(self, message: Message) -> None:
        """Accept incoming messages and store data."""
        if message.type == MessageType.DATA:
            self._data.mergeAtPath(message.data, message.path)

    async def accept(self, tree: SampleTree, path: Path) -> None:
        """Accept sample data at a path."""
        self._data.mergeAtPath(tree, path)

    # MARK: - Storage Interface (Delete)

    def delete(
        self,
        path: Path = Path(),
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None
    ) -> asyncio.Task:
        """Delete data from the storage."""
        node = self._data.existingNode(path)
        if node is not None:
            node.deleteSamples(start, end)
        return asyncio.create_task(asyncio.sleep(0))


async def main():
    storage = InMemoryStorage()

    # Store some data
    await storage.acceptMessage(
        Message.value(Value(21.5), Path.of("weather", "temperature"))
    )
    await storage.acceptMessage(
        Message.value(Value(63), Path.of("weather", "humidity"))
    )
    await storage.acceptMessage(
        Message.value(Value(23.8), Path.of("weather", "temperature"))
    )

    # Read current value
    current = await storage.currentValue(Path.of("weather", "temperature"))
    print(f"Current temperature: {current.value if current else 'None'}")

    # Read history
    samples = await storage.samples(
        Path.of("weather", "temperature"),
        limit=10
    )
    print(f"Temperature history: {[s.value.value for s in samples]}")

    # Read entire tree
    tree = await storage.currentTree(Path.of("weather"), depth=1)
    print("\n=== Current Tree ===")
    print(tree)

    # Delete temperature data
    await storage.delete(Path.of("weather", "temperature"))

    # Verify deletion
    remaining = await storage.currentTree(Path.of("weather"), depth=1)
    print("\n=== After Deletion ===")
    print(remaining)


if __name__ == "__main__":
    asyncio.run(main())
