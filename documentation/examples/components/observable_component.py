"""
Example: Observable Component

Demonstrates how to use the Observable pattern to notify receivers
when data changes.
"""

import asyncio

from soil.data import Path, SampleTree, Timestamp, Value
from soil.components import Observable, Receiver
from soil.messaging import Message


class DataObservable(Observable):
    """An observable that notifies receivers when data changes."""

    def __init__(self):
        super().__init__()
        self._data: SampleTree = SampleTree()

    async def acceptMessage(self, message: Message) -> None:
        """Accept incoming messages and notify receivers."""
        if message.type.value == "data":
            # Update internal data
            self._data.mergeAtPath(message.data, message.path)

            # Notify all receivers about the change
            await self.notifyReceivers(message)

    async def currentValue(self, path: Path) -> Value | None:
        """Get the current value at a path."""
        node = self._data.existingNode(path)
        if node is None:
            return None
        sample = node.newestSample
        return sample.value if sample else None


class LoggingReceiver(Receiver):
    """A receiver that logs all incoming messages."""

    async def acceptMessage(self, message: Message) -> None:
        print(f"Received: {message.type} at {message.path}")
        if message.data:
            print(f"  Data: {message.data}")


async def main():
    # Create observable and receiver
    observable = DataObservable()
    receiver = LoggingReceiver()

    # Connect receiver to observable
    await observable.setReceiver(receiver)

    # Send some data
    await observable.acceptMessage(
        Message.value(Value(21.5), Path.of("sensor", "temperature"))
    )
    await asyncio.sleep(0.1)

    await observable.acceptMessage(
        Message.value(Value(63), Path.of("sensor", "humidity"))
    )
    await asyncio.sleep(0.1)

    # Read current value
    temp = await observable.currentValue(Path.of("sensor", "temperature"))
    print(f"\nCurrent temperature: {temp.value if temp else 'None'}")

    # Change receiver
    new_receiver = LoggingReceiver()
    await observable.setReceiver(new_receiver)

    # New receiver gets subsequent messages
    await observable.acceptMessage(
        Message.value(Value(22.0), Path.of("sensor", "temperature"))
    )


if __name__ == "__main__":
    asyncio.run(main())
