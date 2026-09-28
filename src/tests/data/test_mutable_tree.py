import unittest
from soil.data import Path, Sample, Value, MutableSampleTree, Timestamp, ImmutableSampleTree


sample_list = [Sample(Value(1)), Sample(Value(2))]
children_list = {"chil1": MutableSampleTree(sample_list),
                 "child2": MutableSampleTree([Sample(Value(3))])}

class TestMutableTree(unittest.TestCase):

    def testConstructor(self):
        tree = MutableSampleTree()

        self.assertEqual(tree.samples, list())
        self.assertEqual(tree.children, dict())

    def testSamples(self):
        tree = MutableSampleTree([Sample(Value(1), Timestamp(1,1,1,1,1))])

        self.assertEqual(tree.samples, [Sample(Value(1), Timestamp(1,1,1,1,1))])


    def testChildren(self):
        tree = MutableSampleTree(children={"child1": MutableSampleTree()})

        self.assertEqual(tree.children, {"child1": MutableSampleTree()})


    def testCreate(self):
        tree = MutableSampleTree.create(samples=sample_list, children=children_list) # type: ignore

        self.assertEqual(tree.samples, sample_list)
        self.assertEqual(tree.children, children_list)

    def testIsEmpty(self):
        tree_full = MutableSampleTree.create([Sample(Value(1))])
        tree_empty = MutableSampleTree()

        self.assertFalse(tree_full.isEmpty)
        self.assertTrue(tree_empty.isEmpty)


    def testInsert(self):
        tree = MutableSampleTree(children={"child1": MutableSampleTree()})
        tree.insert(sample_list, Path())
        tree.insert(sample_list, Path.of("child1"))
        child1 = tree.children["child1"]

        self.assertEqual(tree.samples, sample_list)
        self.assertEqual(child1.samples, sample_list)


    def testMerge(self):
        root = MutableSampleTree()
        branch = MutableSampleTree()
        leaf = MutableSampleTree()
        root.merge(branch)
        branch.merge(leaf)

        path, subtree = root.containedTree()

        self.assertEqual(path, Path())
        self.assertIs(subtree, root)

    def testMergeAtPath(self): # BUG?!
        root = MutableSampleTree()
        branch = MutableSampleTree()
        leaf = MutableSampleTree(sample_list)

        root.mergeAtPath(branch, Path())
        root.mergeAtPath(leaf, Path.of("branch"))

        path, subtree = root.containedTree()

        self.assertEqual(path, Path.of('branch'))
        self.assertIs(subtree, root.children['branch'])
        self.assertEqual(subtree.samples, sample_list)

    def testContainedTree(self):
        top = MutableSampleTree.ofValue(Value(123))
        middle = MutableSampleTree(None, {"top": top})
        root = MutableSampleTree(None, {"middle": middle})

        path, t = root.containedTree()
        self.assertEqual(path, Path.of("middle", "top"))
        self.assertEqual(len(t.samples), 1)

    def testChild(self):
        root = MutableSampleTree()
        root.add(MutableSampleTree(), "new_child_from_add")
        root.child("new_child_from_func")

        self.assertTrue(root.existingChild("new_child_from_add"))
        self.assertTrue(root.existingChild("new_child_from_func"))


    def testSaveSamples(self): # __eq__ Timestamp missing!!!
        root = MutableSampleTree()
        sample_list_time = [Sample(Value(1), Timestamp(1,3,1)), Sample(Value(2), Timestamp(1,1,1)), 
                            Sample(Value(1), Timestamp(3,1,1)), Sample(Value(2), Timestamp(2,1,1))]

        root.saveSamples(sample_list_time)

        self.assertEqual(root.samples, [Sample(Value(1), Timestamp(1,1,1)), Sample(Value(2), Timestamp(1,3,1)), 
                            Sample(Value(1), Timestamp(2,1,1)), Sample(Value(2), Timestamp(3,1,1))])


    def testInsertSampleIntoHistory(self):
        root = MutableSampleTree()

        root.insertSampleIntoHistory(sample_list[0])
        self.assertEqual(root.samples, [sample_list[0]])

    def testInsertSampleIntoHistory_timetest_append(self):
        root = MutableSampleTree()
        old_sample = Sample(Value(1), Timestamp(1,1,1))
        new_sample = Sample(Value(0.5), Timestamp(2,2,2))

        root.insertSampleIntoHistory(old_sample)
        root.insertSampleIntoHistory(new_sample)

        self.assertEqual(root.samples, [old_sample, new_sample])

    def testInsertSampleIntoHistory_timetest(self):
        root = MutableSampleTree()
        old_sample = Sample(Value(1), Timestamp(1,1,1))
        new_sample = Sample(Value(0.5), Timestamp(2,2,2))
        middle_sample = Sample(Value(0.5), Timestamp(2,1,2))

        root.insertSampleIntoHistory(new_sample)
        root.insertSampleIntoHistory(old_sample)

        self.assertEqual(root.samples, [old_sample, new_sample])

        root.insertSampleIntoHistory(middle_sample)

        self.assertEqual(root.samples, [old_sample, middle_sample ,new_sample])


    def testTreeInclusionExclusion(self):
        root = MutableSampleTree()
        sample_list_time = [Sample(Value(1), Timestamp(1,3,1)), Sample(Value(2), Timestamp(1,1,2)), 
                            Sample(Value(1), Timestamp(1,1,1)), Sample(Value(2), Timestamp(1,4,1))]
        root.saveSamples(sample_list_time)
        
        compare = root.tree(start=Timestamp(1,1,1), end=Timestamp(1,3,3), depth=None, limitPerNode=None)

        sample_list_time_compare = [Sample(Value(2), Timestamp(1,1,2)), 
                                    Sample(Value(1), Timestamp(1,3,1))]

        self.assertEqual(compare.samples, sample_list_time_compare)
        
    def testTreeDepthZero(self):
        root = MutableSampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 1))])
        child = root.child("sat")
        child.saveSamples([Sample(Value(9), Timestamp(1, 1, 1))])

        result = root.tree(depth=0)

        self.assertEqual(len(result.samples), 1)
        self.assertEqual(result.children, {})


    def testTreeDepthOneTwo(self):
        root = MutableSampleTree()
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
        root = MutableSampleTree()
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
        root = MutableSampleTree()
        result = root.tree()

        self.assertEqual(root, result)


    def testTree_limitZero(self):
        root = MutableSampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 1))])
        result = root.tree(limitPerNode=0)

        self.assertEqual(result.samples, [])


    def testGetSamples(self):
        root = MutableSampleTree()
        root.saveSamples([
            Sample(Value(1), Timestamp(1, 1, 2)),
            Sample(Value(2), Timestamp(1, 2, 1)),
        ])

        result = root.getSamples(start=Timestamp(1, 1, 1), end=Timestamp(1, 3, 1), limit=None)
        self.assertEqual([s.timestamp for s in result], [Timestamp(1, 1, 2), Timestamp(1, 2, 1)])

        result = root.getSamples(start=Timestamp(1, 3, 1), end=Timestamp(1, 1, 1), limit=None)
        self.assertEqual([s.timestamp for s in result], [Timestamp(1, 2, 1), Timestamp(1, 1, 2)])


    def testGetSamplesLimit(self):
        root = MutableSampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1))])

        self.assertEqual(root.getSamples(start=Timestamp(1, 1, 1), end=Timestamp(1, 3, 1), limit=1), [Sample(Value(1), Timestamp(1, 1, 2))])


    def testGetSamplesLimitDescending(self):
        root = MutableSampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1))])

        result = root.getSamples(start=Timestamp(1, 3, 1), end=Timestamp(1, 1, 1), limit=1)
        self.assertEqual(result, [Sample(Value(2), Timestamp(1, 2, 1))])


    def testDelete(self):
        root = MutableSampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1)), Sample(Value(3), Timestamp(2, 2, 1))])
        root.delete(None, None, None)

        self.assertEqual(root.samples, [])

    def testDeleteRangeStartEnd(self):
        root = MutableSampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1)), Sample(Value(3), Timestamp(2, 2, 1))])
        root.delete(Timestamp(1,1,1), Timestamp(1,2,1), None)
        
        self.assertEqual(root.samples, [Sample(Value(3), Timestamp(2, 2, 1))])

    def testDeleteRangeStart(self):
        root = MutableSampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1)), Sample(Value(3), Timestamp(2, 2, 1))])
        root.delete(Timestamp(1,2,1), None, None)
        
        self.assertEqual(root.samples, [Sample(Value(2), Timestamp(1, 1, 3)), Sample(Value(3), Timestamp(2, 2, 1))])

    def testDeleteRangeEnd(self):
        root = MutableSampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1)), Sample(Value(3), Timestamp(2, 2, 1))])
        root.delete(None, Timestamp(1,2,1), None)
        
        self.assertEqual(root.samples, [Sample(Value(3), Timestamp(2, 2, 1))])


    def testDeleteDepth(self):
        root = MutableSampleTree()
        root.saveSamples([Sample(Value(1), Timestamp(1, 1, 2)), Sample(Value(2), Timestamp(1, 2, 1)), Sample(Value(3), Timestamp(2, 2, 1))])
        child = root.child("sat")
        child.saveSamples([Sample(Value(7), Timestamp(1, 1, 5))])

        root.delete(None, None, depth=0)

        self.assertEqual(root.samples, [])
        self.assertEqual(child.samples, [Sample(Value(7), Timestamp(1, 1, 5))])


    def testFindOrCreateNode(self):
        root = MutableSampleTree()

        c = root.findOrCreateNode(Path.of("a", "b", "c"))

        self.assertEqual(list(root.children), ["a"])
        self.assertIs(root.child("a").child("b").child("c"), c)


    def testCreateChild(self):
        root = MutableSampleTree()
        root.createChild("child")

        self.assertEqual(list(root.children), ["child"])


    def testAdd(self):
        root = MutableSampleTree()
        child = MutableSampleTree()
        child.saveSamples(sample_list)

        root.add(child, "child")

        self.assertEqual(list(root.children), ["child"])
        self.assertEqual(root.child("child"), child)


    def testExistingChild(self):
        root = MutableSampleTree()
        child = MutableSampleTree()
        root.add(child, "child")

        child_imm = ImmutableSampleTree()
        root._children["child_imm"] = child_imm

        self.assertEqual(root.existingChild("none"), None)
        self.assertEqual(root.existingChild("child"), child)
        self.assertEqual(root.existingChild("child_imm"), child_imm)
        self.assertIsInstance(root.existingChild("child_imm"), MutableSampleTree)




    def testExistingNode(self):
        root = MutableSampleTree()
        a = root.findOrCreateNode(Path.of("a"))
        ab = root.findOrCreateNode(Path.of("a", "b"))

        self.assertEqual(root.existingNodes(Path.of("a", "b")), [root, a, ab])
        self.assertEqual(root.existingNodes(Path.of("a", "b", "c")), [root, a, ab])
        self.assertEqual(root.existingNodes(Path.of("x")), [root])
        self.assertEqual(root.existingNodes(Path()), [root])   