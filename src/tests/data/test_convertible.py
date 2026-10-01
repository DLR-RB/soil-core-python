import unittest
from soil.data import Path, Sample, Value, SampleTree, Timestamp, SampleTreeConvertible
from soil.data.sampletree import asTree


class MockConvertible(SampleTreeConvertible):
    """
    A simple adopter of SampleTreeConvertible used for testing.

    ``fromTree`` only accepts trees without children,
    so the rejection of improperly structured trees can be tested.
    """

    def __init__(self, tree: SampleTree) -> None:
        self._tree = tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "MockConvertible":
        if tree.children:
            raise ValueError("MockConvertible expects a tree without children")
        return cls(tree)

    def toTree(self) -> SampleTree:
        return self._tree


class TestConvertible(unittest.TestCase):

    def testAdopterWithoutToTree(self):
        """
        A class that does not implement toTree is not a valid adopter.
        """
        class NoToTree(SampleTreeConvertible):

            @classmethod
            def fromTree(cls, tree: SampleTree) -> "NoToTree":
                return None

        self.assertRaises(TypeError, NoToTree)

    def testAdopterWithoutFromTree(self):
        """
        A class that does not implement fromTree is not a valid adopter.
        """
        class NoFromTree(SampleTreeConvertible):

            def toTree(self) -> SampleTree:
                return SampleTree()

        self.assertRaises(TypeError, NoFromTree)


    def testFromTreeToTreeRoundTrip(self):
        """
        A tree converted into an adopter and back
        contains the same samples as the original tree.
        """
        tree = SampleTree([Sample(Value(5))])

        convertible = MockConvertible.fromTree(tree)
        result = convertible.toTree()

        self.assertIsInstance(convertible, SampleTreeConvertible)
        self.assertTrue(result.isEqualTo(tree))

    def testFromTreeRejectsTreeWithChildren(self):
        """
        fromTree rejects trees that don't have the expected structure.
        """
        badTree = SampleTree()
        badTree.child("x")

        with self.assertRaises(ValueError):
            MockConvertible.fromTree(badTree)


    def testAsTreePassesThroughSampleTree(self):
        """
        asTree returns the given tree unchanged, if it is a SampleTree.
        """
        tree = SampleTree()

        self.assertIs(asTree(tree), tree)

    def testAsTreeConvertsConvertible(self):
        """
        asTree converts a SampleTreeConvertible into a SampleTree.
        """
        convertible = MockConvertible(SampleTree([Sample(Value(7))]))

        converted = asTree(convertible)

        self.assertIsInstance(converted, SampleTree)
        self.assertEqual(converted.totalNumberOfSamples, 1)


    def testMergeWithConvertible(self):
        """
        merge accepts a SampleTreeConvertible and merges its tree.
        """
        target = SampleTree()

        target.merge(MockConvertible(SampleTree([Sample(Value(1))])))

        self.assertEqual(target.totalNumberOfSamples, 1)
        self.assertEqual(target.samples[0].value, Value(1))

    def testMergeAtPathWithConvertible(self):
        """
        mergeAtPath accepts a SampleTreeConvertible
        and merges its tree at the given path.
        """
        target = SampleTree()
        path = Path()
        path.append("a")

        target.mergeAtPath(MockConvertible(SampleTree([Sample(Value(1))])), path)

        child = target.existingChild("a")
        self.assertIsNotNone(child)
        self.assertEqual(child.totalNumberOfSamples, 1)

    def testSaveWithConvertible(self):
        """
        save accepts a SampleTreeConvertible and saves its tree.
        """
        target = SampleTree()

        target.save(MockConvertible(SampleTree([Sample(Value(2))])))

        self.assertEqual(len(target.samples), 1)
        self.assertEqual(target.samples[0].value, Value(2))

    def testMergeWithConvertibleWithChildren(self):
        """
        merge converts a convertible with children
        and merges the full subtree.
        """
        target = SampleTree()
        subTree = SampleTree([Sample(Value(2))])
        tree = SampleTree([Sample(Value(1))], {"a": subTree})

        target.merge(MockConvertible(tree))

        self.assertEqual(target.totalNumberOfSamples, 2)
        self.assertEqual(target.numberOfNodesWithSamples, 2)
        child = target.existingChild("a")
        self.assertEqual(child.samples[0].value, Value(2))

    def testMergeWithPlainTree(self):
        """
        Passing a plain SampleTree to merge still works as before.
        """
        target = SampleTree()

        target.merge(SampleTree([Sample(Value(3))]))

        self.assertEqual(target.totalNumberOfSamples, 1)
        self.assertEqual(target.samples[0].value, Value(3))
