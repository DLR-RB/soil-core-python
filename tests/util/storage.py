from asyncio import sleep
from typing import override

from soil.components import Storage
from soil.data import Path, SampleTree, Timestamp
from soil.storage import InMemoryStorage
from soil.utils import Actor, synchronized


class TestStorage(Actor, Storage):
    def __init__(self) -> None:
        Actor.__init__(self)
        self._wrapped = InMemoryStorage()

        self._didRead = False
        self._didWrite = False
        self._didDelete = False

    @override
    async def tree(
        self,
        path: Path,
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
        limitPerNode: int | None = None,
    ) -> SampleTree:
        """
        Retrieve a tree for a given path and interval.

        May take time; uses async internally.

        :param path: The requested path.
        :param start: The start of the interval (exclusive).
        :param end: The end of the interval (inclusive).
        :param depth: The number of levels to include below the path.
        :param limitPerNode: Maximum samples per node.
        :return: A SampleTree.
        """
        result = await self._wrapped.tree(
            path,
            start,
            end,
            depth,
            limitPerNode,
        )

        self._didRead = True

        return result

    @override
    @synchronized
    async def accept(
        self,
        tree: SampleTree,
        path: Path,
    ) -> None:
        result = await self._wrapped.accept(tree, path)
        self._didWrite = True
        return result

    @override
    @synchronized
    async def delete(
        self,
        path: Path = Path(),
        start: Timestamp | None = None,
        end: Timestamp | None = None,
        depth: int | None = None,
    ) -> None:
        """
        Delete data from storage.

        Returns after completion.
        """
        result = await self._wrapped.delete(
            path,
            start,
            end,
            depth,
        )

        self._didDelete = True

        return result

    def didRead(self) -> bool:
        return self._didRead

    def didWrite(self) -> bool:
        return self._didWrite

    def didDelete(self) -> bool:
        return self._didDelete

    async def waitForRead(self) -> bool:
        return await self._waitFor("read")

    async def waitForWrite(self) -> bool:
        return await self._waitFor("write")

    async def waitForDelete(self) -> bool:
        return await self._waitFor("delete")

    def resetWaiting(self) -> None:
        self._didRead = False
        self._didWrite = False
        self._didDelete = False

    async def _waitFor(self, value: str) -> bool:
        tries = 10

        while tries > 0:
            if value == "read" and self._didRead:
                return True

            if value == "write" and self._didWrite:
                return True

            if value == "delete" and self._didDelete:
                return True

            await sleep(0.05)
            tries -= 1

        return False
