import unittest
from unittest.mock import AsyncMock, MagicMock

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
        self._receiver = None  # Initialisierung auf None wichtig

    async def reduce(self, tree: SampleTree, path: Path) -> SampleTree | None:
        self.reduceCalls.append((tree, path))
        return self._reduceResult

    def include(self, path, depth): ...
    def exclude(self, path, depth): ...
    def deleteRules(self, path, depth=None): ...
    async def isSubscribed(self, path): ...

    async def getReceiver(self) -> Receiver | None:
        return self._receiver

    async def setReceiver(self, receiver: Receiver | None) -> None:
        self._receiver = receiver


tree = SampleTree(samples=[Sample(Value(1)), Sample(Value([Value(1)]))], children={"child1": SampleTree([Sample(Value(1))])})


class TestObservable(unittest.IsolatedAsyncioTestCase):

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



    async def test_Distribute_no_Receiver(self):
        mock = Mocker(reduceResult=SampleTree())
        
        await mock.setReceiver(None)
        
        try:
            await mock.distribute(SampleTree(), Path.of("x"))
        except Exception as e:
            self.fail(f"distribute raised unexpectedly: {e}")

    async def test_Distribute_no_Data(self):
        mock = Mocker(reduceResult=None)
        
        mock._receiver = MagicMock() 
        
        await mock.distribute(SampleTree(), Path.of("x"))
        mock._receiver.accept.assert_not_called()

    async def test_Distribute_working(self):
        mock = Mocker(reduceResult=SampleTree(samples=[Sample(Value("ok"))], children={}))
        
        request_mock = MagicMock()
        
        request_mock.wait = AsyncMock(return_value=None) 
        
        receiver_mock = MagicMock()
        receiver_mock.accept.return_value = request_mock
        
        await mock.setReceiver(receiver_mock)

        await mock.distribute(SampleTree(), Path.of("source"))

        self.assertEqual(receiver_mock.accept.call_count, 1)
        
        forwarded_tree, forwarded_path = receiver_mock.accept.call_args[0]
        self.assertIsInstance(forwarded_tree, SampleTree)
        self.assertIsInstance(forwarded_path, Path)
        
        self.assertEqual(request_mock.wait.await_count, 1)