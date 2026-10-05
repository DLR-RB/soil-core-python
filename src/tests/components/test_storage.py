from sqlite3 import Time
from typing import Any
import unittest

from soil.data import Path
from soil.data.sampletree import SampleTree
from soil.data.timestamp import Timestamp
from soil.requests import CompletedRequest, Request

from soil.components.storage import Storage


class MockStorage(Storage):

    def __init__(self):
        self.deleteCalls = []
        self.request = CompletedRequest()

    def delete(self, path=Path(), start=None, end=None, depth=None):
        self.deleteCalls.append((path, start, end, depth))
        return self.request

    def deleteAtRoot(self, start: Timestamp | None, end: Timestamp | None, depth: int | None) -> Request:
        return super().deleteAtRoot(start, end, depth)


    def accept(self, tree: SampleTree, path: Path) -> Request:
        return super().accept(tree, path)

    async def tree(self, path: Path, start: Timestamp | None, end: Timestamp | None, depth: int | None, limitPerNode: int | None) -> SampleTree:
        return await super().tree(path, start, end, depth, limitPerNode)



class testStorage(unittest.TestCase):

    def test_storage_is_abstract(self):
        with self.assertRaises(TypeError):
            Storage()

    def test_delete_at_root_uses_root_path(self):
        storage = MockStorage()

        storage.deleteAtRoot(None, None, None)

        self.assertEqual(len(storage.deleteCalls), 1)
        path = storage.deleteCalls[0][0]
        self.assertTrue(path.isEmpty)
        self.assertEqual(len(path), 0)

    def test_delete_at_root_passes_parameters(self):
        storage = MockStorage()
        start = Timestamp(1, 1, 1)
        end = Timestamp(2, 1, 1)

        storage.deleteAtRoot(start, end, 3)

        path, receivedStart, receivedEnd, depth = storage.deleteCalls[0]
        self.assertIs(start, receivedStart)
        self.assertIs(end, receivedEnd)
        self.assertIs(depth, 3)

    def test_delete_at_root_returns_delete_result(self):
        storage = MockStorage()

        request = storage.deleteAtRoot(None, None, None)

        self.assertIs(request, storage.request)