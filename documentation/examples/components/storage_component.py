"""
Example: Storage Component

Demonstrates how to use the built-in `InMemoryStorage` to store, retrieve,
and delete data through the Provider / Receiver / Storage interfaces.
"""

import asyncio

from soil.data import Path, SampleTree, Value
from soil.storage import InMemoryStorage


async def main():
    storage = InMemoryStorage()

    # Store some data through the Receiver interface. `accept` returns a
    # Request that we wait on before reading it back.
    await storage.accept(
        SampleTree.ofValue(Value(21.5), timestamp=None),
        Path.of("weather", "temperature"),
    ).wait()
    await storage.accept(
        SampleTree.ofValue(Value(63), timestamp=None),
        Path.of("weather", "humidity"),
    ).wait()
    await storage.accept(
        SampleTree.ofValue(Value(23.8), timestamp=None),
        Path.of("weather", "temperature"),
    ).wait()

    # Read the current value through the Provider interface.
    current = await storage.currentValue(Path.of("weather", "temperature"))
    print(f"Current temperature: {current.value if current else 'None'}")

    # Read the history through the Provider interface.
    samples = await storage.samples(
        Path.of("weather", "temperature"),
        limit=10,
    )
    print(f"Temperature history: {[s.value.value for s in samples]}")

    # Read the entire current tree (up to depth=1).
    tree = await storage.currentTree(Path.of("weather"), depth=1)
    print("\n=== Current Tree ===")
    print(tree)

    # Delete the temperature history through the Storage interface.
    await storage.delete(Path.of("weather", "temperature"))

    # Verify deletion.
    remaining = await storage.currentTree(Path.of("weather"), depth=1)
    print("\n=== After Deletion ===")
    print(remaining)

    await storage.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
