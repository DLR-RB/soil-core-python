import unittest
from soil.data import Path, Sample, Value, ImmutableSampleTree, Timestamp


sample_list = [Sample(Value(1)), Sample(Value(2))]
children_list = {"chil1": ImmutableSampleTree(sample_list),
                 "child2": ImmutableSampleTree([Sample(Value(3))])}

class TestImmutableTree(unittest.TestCase):

    def testConstructor(self):
        tree = ImmutableSampleTree()

        self.assertEqual(tree.samples, list())
        self.assertEqual(tree.children, dict())

    def testSamples(self):
        tree = ImmutableSampleTree([Sample(Value(1), Timestamp(1,1,1,1,1))])

        self.assertEqual(tree.samples, [Sample(Value(1), Timestamp(1,1,1,1,1))])


    def testChildren(self):
        tree = ImmutableSampleTree(children={"child1": ImmutableSampleTree()})

        self.assertEqual(tree.children, {"child1": ImmutableSampleTree()})


    def testCreate(self):
        tree = ImmutableSampleTree.create(samples=sample_list, children=children_list) # type: ignore

        self.assertEqual(tree.samples, sample_list)
        self.assertEqual(tree.children, children_list)

    def testIsEmpty(self):
        tree_full = ImmutableSampleTree.create([Sample(Value(1))])
        tree_empty = ImmutableSampleTree()

        self.assertFalse(tree_full.isEmpty)
        self.assertTrue(tree_empty.isEmpty)


    

    


        