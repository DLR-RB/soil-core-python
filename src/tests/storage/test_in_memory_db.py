from random import shuffle
from unittest import main

from soil.components import Storage
from soil.data import Path, Sample, SampleTree, Timestamp, Value
from soil.storage import InMemoryStorage

from ..util import SoilAsyncTest


class InMemoryTests(SoilAsyncTest):

    async def testSingleValue(self):
        storage = InMemoryStorage()

        value = Value(123)
        path = Path.of("a", "b", "c")
        time = Timestamp.current()

        await storage.acceptValue(value, path).wait()

        stored = await storage.tree(path, depth = 0)
        sample = self._require(stored.newestSample)
        self.assertEqual(sample.value, value)
        self.assertTrue(sample.isVeryCloseTo(time, 0.1))
        self.assertEmpty(stored.children)

    async def testCurrentValue(self):
        storage = InMemoryStorage()

        value = Value(123)
        path = Path.of("a", "b", "c")
        time = Timestamp.current()

        await storage.acceptValue(value, path).wait()

        stored = await storage.currentTree(path, depth = 0)
        sample = self._require(stored.newestSample)
        self.assertEqual(sample.value, value)
        self.assertTrue(sample.isVeryCloseTo(time, 0.1))
        self.assertEmpty(stored.children)

    async def testSaveAndGetValueWithTimestamp(self):
        storage = InMemoryStorage()

        value = Value(123)
        path = Path.of("a", "b", "c")
        time = Timestamp.current()

        await storage.acceptValue(value, path, time).wait()

        stored = await storage.tree(path, depth = 0)
        sample = self._require(stored.newestSample)
        self.assertEqual(sample.value, value)
        self.assertTrue(sample.isVeryCloseTo(time))
        self.assertEmpty(stored.children)

    async def testReplaceCurrentValue(self):
        storage = InMemoryStorage()

        newValue = Value(123)
        newTime = Timestamp.current().adding(-1)
        path = Path.of("a", "b", "c")

        oldValue = Value(234)
        oldTime = newTime.adding(-10)

        await storage.acceptValue(oldValue, path, oldTime).wait()

        # Get current value
        stored = await storage.tree(path, depth = 0)
        sample = self._require(stored.newestSample)
        self.assertEqual(sample.value, oldValue)
        self.assertTrue(sample.isVeryCloseTo(oldTime))
        self.assertEmpty(stored.children)

        await storage.acceptValue(newValue, path, newTime).wait()

        # Get current value
        stored = await storage.currentTree(path, depth = 0)
        self.assertSize(stored.samples, 1)
        sample = self._require(stored.newestSample)
        self.assertEqual(sample.value, newValue)
        self.assertTrue(sample.isVeryCloseTo(newTime))
        self.assertEmpty(stored.children)

        # Get old value
        stored = await storage.treeAtTime(path, oldTime.adding(1), depth = 0)
        sample = self._require(stored.newestSample)
        self.assertEqual(sample.value, oldValue)
        self.assertTrue(sample.isVeryCloseTo(oldTime))
        self.assertEmpty(stored.children)


    async def testSaveAndGetRootValue(self):
        storage = InMemoryStorage()

        value = Value(123)
        time = Timestamp.current()
        path = Path()

        await storage.acceptValue(value, path, time).wait()

        stored = await storage.tree(path, depth = 0)
        sample = self._require(stored.newestSample)
        self.assertEqual(sample.value, value)
        self.assertEqual(sample.timestamp, time)
        self.assertEmpty(stored.children)

    async def testStoreTree(self):
        storage = InMemoryStorage()

        now = Timestamp.current()

        cTree = SampleTree.ofValue(value = Value("hello"), timestamp = now)
        fTree = SampleTree.ofValue(value = Value(3.14), timestamp = now)
        bTree = SampleTree(children = {"c" : cTree, "f" : fTree})
        eTree = SampleTree.ofValue(value = Value.path("z", "x"), timestamp = now)
        dTree = SampleTree(children = {"e" : eTree})
        aTree = SampleTree.ofValue(value = Value(123), timestamp = now, children = { "d" : dTree })
        tree = SampleTree(children = {"a" : aTree, "b" : bTree})
        await storage.accept(tree, Path()).wait()


        tree = await storage.tree(Path())
        self. assertSize(tree.children, 2)
        self.assertEmpty(tree.samples)

        a = self._require(tree.children.get("a"))
        aSample = self._require(a.newestSample)
        self.assertEqual(aSample.value, Value(123))
        self.assertTrue(aSample.isVeryCloseTo(now))
        self. assertSize(a.children, 1)

        d = self._require(a.children.get("d"))
        self.assertEmpty(d.samples)
        self. assertSize(d.children, 1)

        e = self._require(d.children.get("e"))
        eSample = self._require(e.newestSample)
        self.assertEqual(eSample.value, Value.path("z", "x"))
        self.assertTrue(eSample.isVeryCloseTo(now))
        self.assertEmpty(e.children)

        b = self._require(tree.children.get("b"))
        self.assertEmpty(b.samples)
        self. assertSize(b.children, 2)

        c = self._require(b.children.get("c"))
        cSample = self._require(c.newestSample)
        self.assertEqual(cSample.value, Value("hello"))
        self.assertTrue(cSample.isVeryCloseTo(now))
        self.assertEmpty(c.children)

        f = self._require(b.children.get("f"))
        fSample = self._require(f.newestSample)
        self.assertEqual(fSample.value, Value(3.14))
        self.assertTrue(fSample.isVeryCloseTo(now))
        self.assertEmpty(f.children)

    async def testGetFullTree(self):
        storage = InMemoryStorage()

        now = Timestamp.current()
        await storage.acceptValue(Value(123), Path.of("a"), now).wait()
        await storage.acceptValue(Value("hello"), Path.of("b", "c"), now).wait()
        await storage.acceptValue(Value.path("z", "x"), Path.of("a", "d", "e"), now).wait()
        await storage.acceptValue(Value(3.14), Path.of("b", "f"), now).wait()


        tree = await storage.tree(Path())
        self. assertSize(tree.children, 2)
        self.assertEmpty(tree.samples)

        a = self._require(tree.children.get("a"))
        aSample = self._require(a.newestSample)
        self.assertEqual(aSample.value, Value(123))
        self.assertTrue(aSample.isVeryCloseTo(now))
        self. assertSize(a.children, 1)

        d = self._require(a.children.get("d"))
        self.assertEmpty(d.samples)
        self. assertSize(d.children, 1)

        e = self._require(d.children.get("e"))
        eSample = self._require(e.newestSample)
        self.assertEqual(eSample.value, Value.path("z", "x"))
        self.assertTrue(eSample.isVeryCloseTo(now))
        self.assertEmpty(e.children)

        b = self._require(tree.children.get("b"))
        self.assertEmpty(b.samples)
        self. assertSize(b.children, 2)

        c = self._require(b.children.get("c"))
        cSample = self._require(c.newestSample)
        self.assertEqual(cSample.value, Value("hello"))
        self.assertTrue(cSample.isVeryCloseTo(now))
        self.assertEmpty(c.children)

        f = self._require(b.children.get("f"))
        fSample = self._require(f.newestSample)
        self.assertEqual(fSample.value, Value(3.14))
        self.assertTrue(fSample.isVeryCloseTo(now))
        self.assertEmpty(f.children)

    async def testGetTreeWithDepth(self):
        storage = InMemoryStorage()

        now = Timestamp.current()
        await storage.acceptValue(Value(123), Path.of("a"), now).wait()
        await storage.acceptValue(Value("hello"), Path.of("b", "c"), now).wait()
        await storage.acceptValue(Value.path("z", "x"), Path.of("a", "d", "e"), now).wait()
        await storage.acceptValue(Value(3.14), Path.of("b", "f"), now).wait()

        tree = await storage.tree(Path(), depth = 0)
        self.assertEmpty(tree.children)
        self.assertEmpty(tree.samples)

        tree = await storage.tree(Path(), depth = 1)
        self. assertSize(tree.children, 2)
        self.assertEmpty(tree.samples)

        a = self._require(tree.children.get("a"))
        aSample = self._require(a.newestSample)
        self.assertEqual(aSample.value, Value(123))
        self.assertTrue(aSample.isVeryCloseTo(now))
        self.assertEmpty(a.children)

        b = self._require(tree.children.get("b"))
        self.assertEmpty(b.samples)
        self.assertEmpty(b.children)

        b = await storage.tree(Path.of("b"), depth = 0)
        self.assertEmpty(b.samples)
        self. assertSize(b.children, 0)

        b = await storage.tree(Path.of("b"), depth = 1)
        self.assertEmpty(b.samples)
        self. assertSize(b.children, 2)

        c = self._require(b.children.get("c"))
        cSample = self._require(c.newestSample)
        self.assertEqual(cSample.value, Value("hello"))
        self.assertTrue(cSample.isVeryCloseTo(now))
        self.assertEmpty(c.children)

        f = self._require(b.children.get("f"))
        fSample = self._require(f.newestSample)
        self.assertEqual(fSample.value, Value(3.14))
        self.assertTrue(fSample.isVeryCloseTo(now))
        self.assertEmpty(f.children)

    async def testGetFullTreeAtTime(self):
        storage = InMemoryStorage()

        now = Timestamp.current()
        old = now.adding(-100)
        queryTime = now.adding(-50)

        # Store old and new values in mixed order
        await storage.acceptValue(Value("there"), Path.of("b", "c"), old).wait()
        await storage.acceptValue(Value(123), Path.of("a"), now).wait()
        await storage.acceptValue(Value("hello"), Path.of("b", "c"), now).wait()
        await storage.acceptValue(Value(234), Path.of("a"), old).wait()
        await storage.acceptValue(Value(42.1), Path.of("b", "f"), old).wait()
        await storage.acceptValue(Value.path("z", "x"), Path.of("a", "d", "e"), now).wait()
        await storage.acceptValue(Value.path("y", "w"), Path.of("a", "d", "e"), old).wait()
        await storage.acceptValue(Value(3.14), Path.of("b", "f"), now).wait()

        # Get current tree
        tree = await storage.tree(Path())
        self. assertSize(tree.children, 2)
        self.assertEmpty(tree.samples)

        a = self._require(tree.children.get("a"))
        aSample = self._require(a.newestSample)
        self.assertEqual(aSample.value, Value(123))
        self.assertTrue(aSample.isVeryCloseTo(now))
        self. assertSize(a.children, 1)

        d = self._require(a.children.get("d"))
        self.assertEmpty(d.samples)
        self. assertSize(d.children, 1)

        e = self._require(d.children.get("e"))
        eSample = self._require(e.newestSample)
        self.assertEqual(eSample.value, Value.path("z", "x"))
        self.assertTrue(eSample.isVeryCloseTo(now))
        self.assertEmpty(e.children)

        b = self._require(tree.children.get("b"))
        self.assertEmpty(b.samples)
        self. assertSize(b.children, 2)

        c = self._require(b.children.get("c"))
        cSample = self._require(c.newestSample)
        self.assertEqual(cSample.value, Value("hello"))
        self.assertTrue(cSample.isVeryCloseTo(now))
        self.assertEmpty(c.children)

        f = self._require(b.children.get("f"))
        fSample = self._require(f.newestSample)
        self.assertEqual(fSample.value, Value(3.14))
        self.assertTrue(fSample.isVeryCloseTo(now))
        self.assertEmpty(f.children)

        # Get old tree
        tree = await storage.treeAtTime(Path(), queryTime)
        self.assertIsNone(tree.newestSample)
        self. assertSize(tree.children, 2)

        a = self._require(tree.children.get("a"))
        aSample = self._require(a.newestSample)
        self.assertEqual(aSample.value, Value(234))
        self.assertTrue(aSample.isVeryCloseTo(old))
        self. assertSize(a.children, 1)

        d = self._require(a.children.get("d"))
        self.assertIsNone(d.newestSample)
        self. assertSize(d.children, 1)

        e = self._require(d.children.get("e"))
        eSample = self._require(e.newestSample)
        self.assertEqual(eSample.value, Value.path("y", "w"))
        self.assertTrue(eSample.isVeryCloseTo(old))
        self.assertEmpty(e.children)

        b = self._require(tree.children.get("b"))
        self.assertIsNone(b.newestSample)
        self. assertSize(b.children, 2)

        c = self._require(b.children.get("c"))
        cSample = self._require(c.newestSample)
        self.assertEqual(cSample.value, Value("there"))
        self.assertTrue(cSample.isVeryCloseTo(old))
        self.assertEmpty(c.children)

        f = self._require(b.children.get("f"))
        fSample = self._require(f.newestSample)
        self.assertEqual(fSample.value, Value(42.1))
        self.assertTrue(fSample.isVeryCloseTo(old))
        self.assertEmpty(f.children)

    async def testGetTreeWithDepthAtTime(self):
        storage = InMemoryStorage()

        now = Timestamp.current()
        old = now.adding(-100)
        queryTime = now.adding(-50)

        # Store old and new values in mixed order
        await storage.acceptValue(Value("there"), Path.of("b", "c"), old).wait()
        await storage.acceptValue(Value(123), Path.of("a"), now).wait()
        await storage.acceptValue(Value("hello"), Path.of("b", "c"), now).wait()
        await storage.acceptValue(Value(234), Path.of("a"), old).wait()
        await storage.acceptValue(Value(42.1), Path.of("b", "f"), old).wait()
        await storage.acceptValue(Value.path("z", "x"), Path.of("a", "d", "e"), now).wait()
        await storage.acceptValue(Value.path("y", "w"), Path.of("a", "d", "e"), old).wait()
        await storage.acceptValue(Value(3.14), Path.of("b", "f"), now).wait()

        root = await storage.treeAtTime(Path(), queryTime, depth = 1)
        self. assertSize(root.children, 2)
        self.assertEmpty(root.samples)

        a = self._require(root.children.get("a"))
        aSample = self._require(a.newestSample)
        self.assertEqual(aSample.value, Value(234))
        self.assertTrue(aSample.isVeryCloseTo(old))
        self.assertSize(a.children, 0)

        b = self._require(root.children.get("b"))
        self.assertEmpty(b.samples)
        self.assertSize(b.children, 0)

        a = await storage.treeAtTime(Path.of("a"), queryTime, depth = 1)
        aSample = self._require(a.newestSample)
        self.assertEqual(aSample.value, Value(234))
        self.assertTrue(aSample.isVeryCloseTo(old))
        self.assertSize(a.children, 1)

        d = self._require(a.children.get("d"))
        self.assertEmpty(d.samples)
        self.assertSize(d.children, 0)

        d = await storage.treeAtTime(Path.of("a", "d"), queryTime, depth = 1)
        self.assertEmpty(d.samples)
        self.assertSize(d.children, 1)

        e = self._require(d.children.get("e"))
        eSample = self._require(e.newestSample)
        self.assertEqual(eSample.value, Value.path("y", "w"))
        self.assertTrue(eSample.isVeryCloseTo(old))
        self.assertEmpty(e.children)

        e = await storage.treeAtTime(Path.of("a", "d", "e"), queryTime, depth = 1)
        eSample = self._require(e.newestSample)
        self.assertEqual(eSample.value, Value.path("y", "w"))
        self.assertTrue(eSample.isVeryCloseTo(old))
        self.assertEmpty(e.children)

        b = await storage.treeAtTime(Path.of("b"), queryTime, depth = 1)
        self.assertEmpty(b.samples)
        self.assertSize(b.children, 2)

        c = self._require(b.children.get("c"))
        cSample = self._require(c.newestSample)
        self.assertEqual(cSample.value, Value("there"))
        self.assertTrue(cSample.isVeryCloseTo(old))
        self.assertEmpty(c.children)

        f = self._require(b.children.get("f"))
        fSample = self._require(f.newestSample)
        self.assertEqual(fSample.value, Value(42.1))
        self.assertTrue(fSample.isVeryCloseTo(old))
        self.assertEmpty(f.children)

    async def testGetFullHistory(self):
        storage = InMemoryStorage()

        old = Timestamp.current().adding(-10)
        values = [Sample(Value(x), old.adding(float(x))) for x in range(10)]

        for sample in values:
            await storage.acceptValue(sample.value, Path.of("a"), sample.timestamp).wait()

        samples = await storage.samples(Path.of("a"))
        self.assertSize(samples, len(values))
        self.assertEqual(samples, values)

        shuffled = list(values)
        shuffle(shuffled)
        # Test shuffled insert
        for sample in shuffled:
            await storage.acceptValue(sample.value, Path.of("b"), sample.timestamp).wait()

        samples = await storage.samples(Path.of("b"))
        self.assertSize(samples, len(values))
        self.assertEqual(samples, values)

    async def _databaseWithShuffledValues(self, count: int = 100, path: Path = Path.of("a")) -> tuple[Storage, Timestamp, Path]:
        storage = InMemoryStorage()

        start = Timestamp.current().adding(-count)
        values = [Sample(Value(x), start.adding(x)) for x in range(count)]

        shuffled = list(values)
        shuffle(shuffled)
        for sample in shuffled:
            await storage.acceptValue(sample.value, path, sample.timestamp).wait()
        return storage, start, path

    async def testGetFullHistoryWithLimit(self):
        storage, start, path = await self._databaseWithShuffledValues()

        samples = await storage.samples(path, start = None, end = None, limit = 10)
        self.assertSize(samples,  10)
        expected = [Sample(Value(x), start.adding(x)) for x in range(10)]
        self.assertEqual(samples, expected)

    async def testGetHistoryWithStart(self):
        storage, start, path = await self._databaseWithShuffledValues()

        begin = start.adding(49.5)
        samples = await storage.samples(path, start = begin, end = None, limit = None)
        self.assertSize(samples, 50)
        expected = [Sample(Value(x + 50), start.adding(x + 50)) for x in range(50)]
        self.assertEqual(samples, expected)

    async def testGetHistoryWithStartAndLimit(self):
        storage, start, path = await self._databaseWithShuffledValues()

        begin = start.adding(49.5)
        samples = await storage.samples(path, start = begin, end = None, limit = 20)
        self.assertSize(samples, 20)
        expected = [Sample(Value(x + 50), start.adding(x + 50)) for x in range(20)]
        self.assertEqual(samples, expected)

    async def testGetEmptyHistoryWithStart(self):
        storage, start, path = await self._databaseWithShuffledValues()

        begin = start.adding(100)
        samples = await storage.samples(path, start = begin, end = None, limit = None)
        self.assertEmpty(samples)

    async def testGetHistoryWithEnd(self):
        """
        When requesting history with only the end date set, then we expect descending order of the results.
        """
        storage, start, path = await self._databaseWithShuffledValues()

        end = start.adding(49.5)
        samples = await storage.samples(path, start = None, end = end, limit = None)
        self.assertSize(samples, 50)
        expected = list(reversed([Sample(Value(x), start.adding(x)) for x in range(50)]))
        self.assertEqual(samples, expected)

    async def testGetHistoryWithEndAndLimit(self):
        """
        When requesting history with only the end date set and a limit,
        then we expect descending order of the results,
        limited from the latest timestamps
        """
        storage, start, path = await self._databaseWithShuffledValues()

        end = start.adding(49.5)
        samples = await storage.samples(path, start = None, end = end, limit = 20)
        self.assertSize(samples, 20)
        expected = list(reversed([Sample(Value(x), start.adding(x)) for x in range(30, 50)]))
        self.assertEqual(samples, expected)

    async def testGetEmptyHistoryWithEnd(self):
        storage, start, path = await self._databaseWithShuffledValues()

        end = start.adding(-10)
        samples = await storage.samples(path, start = None, end = end, limit = None)
        self.assertEmpty(samples)

    async def testGetHistoryInInterval(self):
        storage, start, path = await self._databaseWithShuffledValues()

        begin = start.adding(49.5)
        end = begin.adding(20)
        samples = await storage.samples(path, start = begin, end = end, limit = None)
        self.assertSize(samples,  20)
        expected = [Sample(Value(x + 50), start.adding(x + 50)) for x in range(20)]
        self.assertEqual(samples, expected)

    async def testGetHistoryInIntervalWithLimit(self):
        storage, start, path = await self._databaseWithShuffledValues()

        begin = start.adding(49.5)
        end = begin.adding(20)
        samples = await storage.samples(path, start = begin, end = end, limit = 10)
        self.assertSize(samples, 10)
        expected = [Sample(Value(x + 50), start.adding(x + 50)) for x in range(10)]
        self.assertEqual(samples, expected)

    async def testGetEmptyHistoryInInterval(self):
        storage, start, path = await self._databaseWithShuffledValues()

        begin = start.adding(-20)
        end = begin.adding(-10)
        samples = await storage.samples(path, start = begin, end = end, limit = None)
        self.assertEmpty(samples)

    async def testGetEmptyHistoryInReversedInterval(self):
        storage, start, path = await self._databaseWithShuffledValues()

        begin = start.adding(-10)
        end = begin.adding(-20)
        samples = await storage.samples(path, start = begin, end = end, limit = None)
        self.assertEmpty(samples)

    async def testGetReversedHistoryInInterval(self):
        storage, start, path = await self._databaseWithShuffledValues()

        begin = start.adding(69.5)
        end = begin.adding(-20)
        samples = await storage.samples(path, start = begin, end = end, limit = 10)
        self.assertSize(samples, 10)
        expected = list(reversed([Sample(Value(x), start.adding(x)) for x in range(60, 70)]))
        self.assertEqual(samples, expected)


if __name__ == "__main__":
    main()
