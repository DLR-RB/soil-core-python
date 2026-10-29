import unittest

from soil.data import Path, Sample, SampleTree, Timestamp, Value

sample_list = [Sample(Value(1)), Sample(Value(2))]
children_list = {"chil1": SampleTree(sample_list),
                 "child2": SampleTree([Sample(Value(3))])}

class TestSampleTree(unittest.TestCase):

    def testConstructor(self):
        tree = SampleTree()

        self.assertEqual(tree.samples, list())
        self.assertEqual(tree.children, dict())

    def testSamples(self):
        tree = SampleTree([Sample(Value(1), Timestamp(1,1,1,1,1))])

        self.assertEqual(tree.samples, [Sample(Value(1), Timestamp(1,1,1,1,1))])


    def testChildren(self):
        tree = SampleTree(children={"child1": SampleTree()})

        self.assertEqual(tree.children, {"child1": SampleTree()})


    def testCreate(self):
        tree = SampleTree.create(samples=sample_list, children=children_list) # type: ignore

        self.assertEqual(tree.samples, sample_list)
        self.assertEqual(tree.children, children_list)

    def testIsEmpty(self):
        tree_full = SampleTree.create([Sample(Value(1))])
        tree_empty = SampleTree()

        self.assertFalse(tree_full.isEmpty)
        self.assertTrue(tree_empty.isEmpty)


    def testInsert(self):
        tree = SampleTree(children={"child1": SampleTree()})
        tree.insert(sample_list, Path())
        tree.insert(sample_list, Path.of("child1"))
        child1 = tree.children["child1"]

        self.assertEqual(tree.samples, sample_list)
        self.assertEqual(child1.samples, sample_list)


    def testMerge(self):
        root = SampleTree()
        branch = SampleTree()
        leaf = SampleTree()
        root.merge(branch)
        branch.merge(leaf)

        path, subtree = root.containedTree()

        self.assertEqual(path, Path())
        self.assertIs(subtree, root)

    def testMergeAtPath(self): # BUG?!
        root = SampleTree()
        branch = SampleTree()
        leaf = SampleTree(sample_list)

        root.mergeAtPath(branch, Path())
        root.mergeAtPath(leaf, Path.of("branch"))

        path, subtree = root.containedTree()

        self.assertEqual(path, Path.of('branch'))
        self.assertIs(subtree, root.children['branch'])
        self.assertEqual(subtree.samples, sample_list)

    def testContainedTree(self):
        top = SampleTree.ofValue(Value(123))
        middle = SampleTree(None, {"top": top})
        root = SampleTree(None, {"middle": middle})

        path, t = root.containedTree()
        self.assertEqual(path, Path.of("middle", "top"))
        self.assertEqual(len(t.samples), 1)

    def testChild(self):
        root = SampleTree()
        root.add(SampleTree(), "new_child_from_add")
        root.child("new_child_from_func")

        self.assertTrue(root.existingChild("new_child_from_add"))
        self.assertTrue(root.existingChild("new_child_from_func"))


    def testSaveSamples(self):
        root = SampleTree()
        sample_list_time = [Sample(Value(1), Timestamp(1,3,1)), Sample(Value(2), Timestamp(1,1,1)), 
                            Sample(Value(1), Timestamp(3,1,1)), Sample(Value(2), Timestamp(2,1,1))]

        root.saveSamples(sample_list_time)

        self.assertEqual(root.samples, [Sample(Value(2), Timestamp(1,1,1)),
                                        Sample(Value(1), Timestamp(1,3,1)),
                                        Sample(Value(2), Timestamp(2,1,1)),
                                        Sample(Value(1), Timestamp(3,1,1))])


    def testInsertSampleIntoHistory(self):
        root = SampleTree()

        root.insertSampleIntoHistory(sample_list[0])
        self.assertEqual(root.samples, [sample_list[0]])

    def testInsertSampleIntoHistory_timetest_append(self):
        root = SampleTree()
        old_sample = Sample(Value(1), Timestamp(1,1,1))
        new_sample = Sample(Value(0.5), Timestamp(2,2,2))

        root.insertSampleIntoHistory(old_sample)
        root.insertSampleIntoHistory(new_sample)

        self.assertEqual(root.samples, [old_sample, new_sample])

    def testInsertSampleIntoHistory_timetest(self):
        root = SampleTree()
        old_sample = Sample(Value(1), Timestamp(1,1,1))
        new_sample = Sample(Value(0.5), Timestamp(2,2,2))
        middle_sample = Sample(Value(0.5), Timestamp(2,1,2))

        root.insertSampleIntoHistory(new_sample)
        root.insertSampleIntoHistory(old_sample)

        self.assertEqual(root.samples, [old_sample, new_sample])

        root.insertSampleIntoHistory(middle_sample)

        self.assertEqual(root.samples, [old_sample, middle_sample ,new_sample])


    def testTreeInclusionExclusion(self):
        root = SampleTree()
        sample_list_time = [Sample(Value(1), Timestamp(1,3,1)), Sample(Value(2), Timestamp(1,1,2)), 
                            Sample(Value(1), Timestamp(1,1,1)), Sample(Value(2), Timestamp(1,4,1))]
        root.saveSamples(sample_list_time)
        
        compare = root.tree(start=Timestamp(1,1,1), end=Timestamp(1,3,3), depth=None, limitPerNode=None)

        sample_list_time_compare = [Sample(Value(2), Timestamp(1,1,2)), 
                                    Sample(Value(1), Timestamp(1,3,1))]

        self.assertEqual(compare.samples, sample_list_time_compare)
        
    def testTreeDepthZero(self):
        root = SampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 1))])
        child = root.child("sat")
        child.saveSamples([Sample(Value(9), Timestamp(1, 1, 1))])

        result = root.tree(depth=0)

        self.assertEqual(len(result.samples), 1)
        self.assertEqual(result.children, {})


    def testTreeDepthOneTwo(self):
        root = SampleTree()
        root.saveSamples([Sample(Value(0), Timestamp(1, 1, 1))])
        child = root.child("sat")
        child.saveSamples([Sample(Value(1), Timestamp(1, 1, 1))])
        grandchild = child.child("telemetry")
        grandchild.saveSamples([Sample(Value(2), Timestamp(1, 1, 1))])

        result1 = root.tree(depth=1)
        result2 = root.tree(depth=2)

        self.assertIn("sat", result1.children)
        self.assertNotIn("telemetry", result1.children["sat"].children)

        self.assertIn("sat", result2.children)
        self.assertIn("telemetry", result2.children["sat"].children)


    def testTreeLimitNode(self):
        root = SampleTree()
        root.saveSamples([
            Sample(Value(1), Timestamp(1, 1, 1)),
            Sample(Value(2), Timestamp(1, 2, 1)),
            Sample(Value(3), Timestamp(1, 3, 1)), 
        ])
        child = root.child("sat")
        child.saveSamples([
            Sample(Value(10), Timestamp(1, 1, 1)),
            Sample(Value(20), Timestamp(1, 2, 1)),
        ])

        result = root.tree(limitPerNode=2)

        self.assertEqual(len(result.samples), 2)       
        self.assertEqual(result.children["sat"].samples, [Sample(Value(10), Timestamp(1, 1, 1)),
                                                          Sample(Value(20), Timestamp(1, 2, 1))])


    def testTreeEmpty(self):
        root = SampleTree()
        result = root.tree()

        self.assertEqual(root, result)


    def testTree_limitZero(self):
        root = SampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 1))])
        result = root.tree(limitPerNode=0)

        self.assertEqual(result.samples, [])


    def testGetSamples(self):
        root = SampleTree()
        root.saveSamples([
            Sample(Value(1), Timestamp(1, 1, 2)),
            Sample(Value(2), Timestamp(1, 2, 1)),
        ])

        result = root.getSamples(start=Timestamp(1, 1, 1), end=Timestamp(1, 3, 1), limit=None)
        self.assertEqual([s.timestamp for s in result], [Timestamp(1, 1, 2), Timestamp(1, 2, 1)])

        result = root.getSamples(start=Timestamp(1, 3, 1), end=Timestamp(1, 1, 1), limit=None)
        self.assertEqual([s.timestamp for s in result], [Timestamp(1, 2, 1), Timestamp(1, 1, 2)])


    def testGetSamplesLimit(self):
        root = SampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1))])

        self.assertEqual(root.getSamples(start=Timestamp(1, 1, 1), end=Timestamp(1, 3, 1), limit=1), [Sample(Value(1), Timestamp(1, 1, 2))])


    def testGetSamplesLimitDescending(self):
        root = SampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1))])

        result = root.getSamples(start=Timestamp(1, 3, 1), end=Timestamp(1, 1, 1), limit=1)
        self.assertEqual(result, [Sample(Value(2), Timestamp(1, 2, 1))])


    def testDelete(self):
        root = SampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1)), Sample(Value(3), Timestamp(2, 2, 1))])
        root.delete(None, None, None)

        self.assertEqual(root.samples, [])

    def testDeleteRangeStartEnd(self):
        root = SampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1)), Sample(Value(3), Timestamp(2, 2, 1))])
        root.delete(Timestamp(1,1,1), Timestamp(1,2,1), None)
        
        self.assertEqual(root.samples, [Sample(Value(3), Timestamp(2, 2, 1))])

    def testDeleteRangeStart(self):
        root = SampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1)), Sample(Value(3), Timestamp(2, 2, 1))])
        root.delete(Timestamp(1,2,1), None, None)
        
        self.assertEqual(root.samples, [Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1))])

        
    def testDeleteRangeEnd(self):
        root = SampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1)), Sample(Value(3), Timestamp(2, 2, 1))])
        root.delete(None, Timestamp(1,2,1), None)
        
        self.assertEqual(root.samples, [Sample(Value(3), Timestamp(2, 2, 1))])


    def testDeleteDepth(self):
        root = SampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1)), Sample(Value(3), Timestamp(2, 2, 1))])
        child = root.child("sat")
        child.saveSamples([Sample(Value(7), Timestamp(1, 1, 5))])

        root.delete(None, None, depth=0)

        self.assertEqual(root.samples, [])
        self.assertEqual(child.samples, [Sample(Value(7), Timestamp(1, 1, 5))])


    def testFindOrCreateNode(self):
        root = SampleTree()

        c = root.findOrCreateNode(Path.of("a", "b", "c"))

        self.assertEqual(list(root.children), ["a"])
        self.assertIs(root.child("a").child("b").child("c"), c)


    def testCreateChild(self):
        root = SampleTree()
        root.createChild("child")

        self.assertEqual(list(root.children), ["child"])


    def testAdd(self):
        root = SampleTree()
        child = SampleTree()
        child.saveSamples(sample_list)

        root.add(child, "child")

        self.assertEqual(list(root.children), ["child"])
        self.assertEqual(root.child("child"), child)


    def testExistingChild(self):
        root = SampleTree()
        child = SampleTree()
        root.add(child, "child")

        child_imm = SampleTree()
        root._children["child_imm"] = child_imm

        self.assertEqual(root.existingChild("none"), None)
        self.assertEqual(root.existingChild("child"), child)
        self.assertEqual(root.existingChild("child_imm"), child_imm)
        self.assertIsInstance(root.existingChild("child_imm"), SampleTree)




    def testExistingNode(self):
        root = SampleTree()
        a = root.findOrCreateNode(Path.of("a"))
        ab = root.findOrCreateNode(Path.of("a", "b"))

        self.assertEqual(root.existingNodes(Path.of("a", "b")), [root, a, ab])
        self.assertEqual(root.existingNodes(Path.of("a", "b", "c")), [root, a, ab])
        self.assertEqual(root.existingNodes(Path.of("x")), [root])
        self.assertEqual(root.existingNodes(Path()), [root])   


    def testDeleteDepthOne(self):
        """ depth=1: Root und eine Ebene werden gelöscht, Enkel bleiben """
        root = SampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2))])
        child = root.child("sat")
        child.saveSamples([Sample(Value(7), Timestamp(1, 1, 5))])
        grandchild = child.child("temp")
        grandchild.saveSamples([Sample(Value(9), Timestamp(1, 1, 6))])

        root.delete(None, None, depth=1)

        self.assertEqual(root.samples, [])
        self.assertEqual(child.samples, [])
        self.assertEqual(grandchild.samples, [Sample(Value(9), Timestamp(1, 1, 6))])

    def testDeleteUnlimitedDepth(self):
        """ depth=None: der komplette Baum wird gelöscht, egal wie tief """
        root = SampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2))])
        child = root.child("sat")
        child.saveSamples([Sample(Value(7), Timestamp(1, 1, 5))])
        grandchild = child.child("temp")
        grandchild.saveSamples([Sample(Value(9), Timestamp(1, 1, 6))])

        root.delete(None, None, depth=None)

        self.assertEqual(root.samples, [])
        self.assertEqual(child.samples, [])
        self.assertEqual(grandchild.samples, [])


class ConvenienceConstructionTests(unittest.TestCase):
    """addChildValue, addChildSamples, addSample, mergeChild."""

    def test_addChildValue_withRawInt(self):
        tree = SampleTree()
        child = tree.addChildValue("temperature", 123)
        self.assertIs(tree.children["temperature"], child)
        self.assertEqual(child.currentValue, Value(123))

    def test_addChildValue_withFalsyValues(self):
        tree = SampleTree()
        tree.addChildValue("zero", 0)
        tree.addChildValue("empty", "")
        self.assertEqual(tree.getChildValue("zero"), Value(0))
        self.assertEqual(tree.getChildValue("empty"), Value(""))

    def test_addChildValue_withValueObject(self):
        tree = SampleTree()
        tree.addChildValue("name", Value("abc"))
        value = tree.getChildValue("name")
        self.assertIsNotNone(value)
        if value is not None:
            self.assertEqual(value.stringValue, "abc")

    def test_addChildValue_overwritesExistingChild(self):
        tree = SampleTree()
        tree.addChildValue("state", 1)
        tree.addChildValue("state", 2)
        self.assertEqual(len(tree.children), 1)
        self.assertEqual(tree.getChildValue("state"), Value(2))

    def test_addChildValue_withTimestamp(self):
        time = Timestamp.fromTimeIntervalSince1970(1000.0)
        tree = SampleTree()
        tree.addChildValue("sampled", 5, time)
        child = tree.existingChild("sampled")
        self.assertIsNotNone(child)
        sample = child.currentSample if child is not None else None
        self.assertIsNotNone(sample)
        if sample is not None and sample.timestamp is not None:
            self.assertTrue(sample.timestamp.isVeryCloseTo(time))

    def test_addChildValue_chaining(self):
        tree = SampleTree()
        tree.addChildValue("gps", 1).addChildValue("lat", 48.2)
        self.assertEqual(tree.getChildValue("gps"), Value(1))
        gps = tree.existingChild("gps")
        self.assertIsNotNone(gps)
        if gps is not None:
            self.assertEqual(gps.getChildValue("lat"), Value(48.2))

    def test_addChildSamples(self):
        tree = SampleTree()
        samples = [
            Sample(Value(1), Timestamp.fromTimeIntervalSince1970(1.0)),
            Sample(Value(2), Timestamp.fromTimeIntervalSince1970(2.0)),
            Sample(Value(3), Timestamp.fromTimeIntervalSince1970(3.0)),
        ]
        child = tree.addChildSamples("history", samples)
        self.assertIs(tree.children["history"], child)
        self.assertEqual(len(child.samples), 3)
        tree.addChildSamples("history", samples[:1])
        replaced = tree.existingChild("history")
        self.assertIsNotNone(replaced)
        if replaced is not None:
            self.assertEqual(len(replaced.samples), 1)  # ersetzt, nicht anhängt

    def test_addSample_withoutTimestamp_keepsHistorySorted(self):
        tree = SampleTree()
        tree.addSample(3, Timestamp.fromTimeIntervalSince1970(30.0))
        tree.addSample(1, Timestamp.fromTimeIntervalSince1970(10.0))
        tree.addSample(2, Timestamp.fromTimeIntervalSince1970(20.0))
        self.assertEqual([s.value for s in tree.samples], [Value(1), Value(2), Value(3)])

    def test_addSample_withRawValue(self):
        tree = SampleTree()
        tree.addSample(42)
        self.assertEqual(tree.currentValue, Value(42))

    def test_mergeChild_createsChild(self):
        tree = SampleTree()
        other = SampleTree.ofValue(Value(1))
        child = tree.mergeChild("merged", other)
        self.assertEqual(tree.getChildValue("merged"), Value(1))
        self.assertIs(tree.existingChild("merged"), child)

    def test_mergeChild_mergesInsteadOfReplacing(self):
        tree = SampleTree()
        tree.addChildValue("data", 1)
        tree.mergeChild("data", SampleTree.ofValue(Value(2)))
        child = tree.existingChild("data")
        self.assertIsNotNone(child)
        if child is not None:
            self.assertEqual(len(child.samples), 2)  # nichts ersetzt


class ConvenienceRetrievalTests(unittest.TestCase):
    """getChildValue, getChildSamples, getChildSample, valueAtPath, sampleAtPath, samplesAtPath, firstSample, currentValue."""

    def test_getChildValue_missingChildReturnsNone(self):
        self.assertIsNone(SampleTree().getChildValue("nope"))

    def test_getChildValue_childWithoutSamplesReturnsNone(self):
        tree = SampleTree()
        tree.createChild("empty")
        self.assertIsNone(tree.getChildValue("empty"))

    def test_getChildSamples_returnsCopy(self):
        tree = SampleTree()
        tree.addChildValue("x", 1)
        result = tree.getChildSamples("x")
        self.assertIsNotNone(result)
        if result is not None:
            result.append(Sample(Value(2)))
            x = tree.existingChild("x")
            self.assertIsNotNone(x)
            if x is not None:
                self.assertEqual(len(x.samples), 1)

    def test_getChildSamples_missingChildReturnsNone(self):
        self.assertIsNone(SampleTree().getChildSamples("nope"))

    def test_getChildSample(self):
        tree = SampleTree()
        tree.addChildValue("x", 42)
        sample = tree.getChildSample("x")
        self.assertIsNotNone(sample)
        if sample is not None:
            self.assertEqual(sample.value, Value(42))
        self.assertIsNone(tree.getChildSample("missing"))

    def test_valueAtPath_and_sampleAtPath(self):
        tree = SampleTree()
        tree.addChildValue("gps", 1).addChildValue("lat", 48.2)
        self.assertEqual(tree.valueAtPath(Path.of("gps", "lat")), Value(48.2))
        self.assertIsNotNone(tree.sampleAtPath(Path.of("gps", "lat")))
        self.assertIsNone(tree.valueAtPath(Path.of("gps", "missing")))
        self.assertIsNone(tree.sampleAtPath(Path.of("nope")))

    def test_samplesAtPath_returnsCopy(self):
        tree = SampleTree()
        tree.addSample(1, Timestamp.fromTimeIntervalSince1970(1.0))
        result = tree.samplesAtPath(Path())
        self.assertIsNotNone(result)
        if result is not None:
            result.clear()
            self.assertEqual(len(tree.samples), 1)

    def test_samplesAtPath_missingPathReturnsNone(self):
        self.assertIsNone(SampleTree().samplesAtPath(Path.of("a")))

    def test_firstSample(self):
        tree = SampleTree()
        tree.addSample(2, Timestamp.fromTimeIntervalSince1970(20.0))
        tree.addSample(1, Timestamp.fromTimeIntervalSince1970(10.0))
        first = tree.firstSample
        self.assertIsNotNone(first)
        if first is not None:
            self.assertEqual(first.value, Value(1))
        self.assertIsNone(SampleTree().firstSample)

    def test_currentValue_returnsValueInstance(self):
        tree = SampleTree.ofValue(Value(123))
        self.assertIsInstance(tree.currentValue, Value)
        self.assertIsNone(SampleTree().currentValue)


class SearchTests(unittest.TestCase):
    """findNodes, nodesBelow."""

    def _buildTree(self) -> SampleTree:
        tree = SampleTree()
        tree.addChildValue("temp", 1).addChildValue("temp", 2)
        tree.addChildValue("gps", 1).addChildValue("temp", 3)
        tree.addChildValue("other", 0)
        return tree

    def test_findNodes_multipleHits(self):
        tree = self._buildTree()
        hits = tree.findNodes("temp")
        paths = [str(path) for path, _ in hits]
        self.assertEqual(len(hits), 3)
        self.assertIn("temp > temp", paths)
        self.assertIn("gps > temp", paths)
        self.assertIn("temp", paths)

    def test_findNodes_noHit(self):
        self.assertEqual(SampleTree().findNodes("x"), [])

    def test_nodesBelow_includesPrefixNode_andFullPaths(self):
        tree = self._buildTree()
        entries = tree.nodesBelow(Path.of("gps"))
        paths = [str(path) for path, _ in entries]
        self.assertEqual(paths[0], "gps")
        self.assertEqual(paths[1], "gps > temp")

    def test_nodesBelow_missingPrefixReturnsEmpty(self):
        tree = self._buildTree()
        self.assertEqual(tree.nodesBelow(Path.of("nope")), [])

    def test_nodesBelow_rootPathReturnsWholeTree(self):
        tree = self._buildTree()
        entries = tree.nodesBelow(Path())
        self.assertEqual(len(entries), 6)

    def test_search_doesNotMutateTree(self):
        tree = self._buildTree()
        tree.findNodes("temp")
        tree.nodesBelow(Path.of("gps"))
        self.assertEqual(tree.totalNumberOfSamples, 5)


if __name__ == "__main__":
    unittest.main()