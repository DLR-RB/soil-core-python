from typing import Dict, List, TypeVar
from unittest import IsolatedAsyncioTestCase, TestCase

T = TypeVar('T')


class SoilTest(TestCase):

    def _require(self, value: T | None) -> T:
        self.assertIsNotNone(value)
        if value is None: raise ValueError("")
        return value

    def assertEmpty(self, lst: List[T] | Dict[str, T]) -> None:
        self.assertSize(lst, 0)

    def assertSize(self, lst: List[T] | Dict[str, T], count: int) -> None:
        self.assertEqual(len(lst), count)



class SoilAsyncTest(IsolatedAsyncioTestCase):

    def _require(self, value: T | None) -> T:
        self.assertIsNotNone(value)
        if value is None: raise ValueError("")
        return value

    def assertEmpty(self, lst: List[T] | Dict[str, T]) -> None:
        self.assertSize(lst, 0)

    def assertSize(self, lst: List[T] | Dict[str, T], count: int) -> None:
        self.assertEqual(len(lst), count)
