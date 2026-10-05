import unittest

from soil.components.observable import Observable
from soil.components.receiver import Receiver
from soil.data import Path, SampleTree
from soil.data.sample import Sample
from soil.data.value import Value

# Helper

class Mocker(Observable):

    def __init__(self, reduceResult: SampleTree | None) -> None:
        super().__init__()
        self._reduceResult = reduceResult
        self.reduceCalls: list[tuple[SampleTree, Path]] = []

    async def reduce(self, tree: SampleTree, path: Path) -> SampleTree | None:
        self.reduceCalls.append((tree, path))
        return self._reduceResult

    def include(self, path, depth): ...
    def exclude(self, path, depth): ...
    def deleteRules(self, path, depth=None): ...
    async def isSubscribed(self, path): ...
    def getReceiver(self): ...
    def setReceiver(self, receiver: Receiver | None): ...

tree = SampleTree(samples=[Sample(Value(1)), Sample(Value([Value(1)]))], children={"child1": SampleTree([Sample(Value(1))])})


class testObservable(unittest.IsolatedAsyncioTestCase):

    async def test_DataForReceiver(self):
        mock = Mocker(reduceResult=None)

        result = await mock.dataForReceiver(SampleTree(), Path())

        self.assertIsNone(result)

        path = Path.of("a", "b")
        mock = Mocker(reduceResult=tree)

        await mock.dataForReceiver(tree, path)

        self.assertEqual(len(mock.reduceCalls), 1)
        calledTree, calledPath = mock.reduceCalls[0]
        self.assertIs(calledTree, tree)
        self.assertEqual(calledPath, path)



        