import unittest
from unittest import mock

from soil.components import Provider
from soil.data import Path, Sample, SampleTree, Timestamp, Value


class MockProvider(Provider):
    def __init__(self, return_value: SampleTree | None = None) -> None:
        super().__init__()
        self._mock_tree_result = return_value or SampleTree()
        self.call_args: list[tuple] = []

    async def tree(
        self, path: Path, start: Timestamp | None, end: Timestamp | None,
        depth: int | None, limitPerNode: int | None
    ) -> SampleTree:
        self.call_args.append((path, start, end, depth, limitPerNode))
        return self._mock_tree_result


class TestProvider(unittest.IsolatedAsyncioTestCase):

    async def test_treeAtTime_calls_tree_with_correct_params(self):
        provider = MockProvider()
        target_time = Timestamp(1,1,1)
        
        await provider.treeAtTime(Path.of("a", "b"), target_time)
        
        calls = provider.call_args
        self.assertEqual(len(calls), 1)
        path, start, end, depth, limit = calls[0]
        
        self.assertEqual(path, Path.of("a", "b"))
        self.assertIsNone(start)
        self.assertEqual(end, target_time)
        self.assertIsNone(depth)
        self.assertEqual(limit, 1)

    async def test_treeAtTime_returns_tree(self):
        provider = MockProvider(return_value=SampleTree(samples=[Sample(Value("test"))]))
        result = await provider.treeAtTime(Path.of("x"), Timestamp.current())
        
        self.assertIsInstance(result, SampleTree)
        self.assertEqual(len(result.samples), 1)

    async def test_samples_calls_tree_with_depth_zero(self):
        provider = MockProvider()
        await provider.samples(Path.of("z"), limit=50)
        
        path, _, _, depth, limit = provider.call_args[0]
        self.assertEqual(path, Path.of("z"))
        self.assertEqual(depth, 0) 
        self.assertEqual(limit, 50)

    async def test_sample_returns_first_sample(self):
        tree_with_two_samples = SampleTree(samples=[
            Sample(Value("oldest")),
            Sample(Value("newest"))
        ])
        provider = MockProvider(return_value=tree_with_two_samples)
        
        sample = await provider.sample(Path.of("x"), Timestamp.current())
        
        self.assertEqual(sample, Sample(Value("oldest")))

    async def test_sample_returns_none_if_empty(self):
        provider = MockProvider(return_value=SampleTree())
        
        sample = await provider.sample(Path.of("x"), Timestamp.current())
        self.assertIsNone(sample)

    async def test_currentTree_calls_tree_with_infinite_past(self):
        provider = MockProvider()
        
        await provider.currentTree(Path.of("x"), depth=2)
        
        path, start, end, depth, limit = provider.call_args[0]
        
        self.assertEqual(path, Path.of("x"))
        self.assertEqual(depth, 2)
        self.assertIsNone(start)
        self.assertIsNotNone(end)
        self.assertEqual(limit, 1)

    async def test_currentSample_calls_tree_with_current_time(self):
        provider = MockProvider(return_value=SampleTree(samples=[Sample(Value(42))]))
        
        await provider.currentSample(Path.of("current"))
        
        path, _, _, depth, limit = provider.call_args[0]
        
        self.assertEqual(path, Path.of("current"))          
        self.assertEqual(depth, 0)
        self.assertEqual(limit, 1) 

    async def test_currentValue_returns_value_if_exists(self):
        expected_val = Value("test_payload")
        provider = MockProvider(return_value=SampleTree(samples=[Sample(expected_val)]))
        
        result = await provider.currentValue(Path.of("x"))
        
        self.assertEqual(result, expected_val)

    async def test_currentValue_returns_none_if_no_samples(self):
        provider = MockProvider(return_value=SampleTree())
        
        result = await provider.currentValue(Path.of("empty"))
        
        self.assertIsNone(result)