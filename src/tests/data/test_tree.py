from unittest import TestCase, main

from soil.data import ImmutableSampleTree, Path, Value


class TreeTests(TestCase):

    def testContainedTree(self):
        top = ImmutableSampleTree.ofValue(Value(123))
        middle = ImmutableSampleTree(None, {"top": top})
        root = ImmutableSampleTree(None, {"middle": middle})

        path, t = root.containedTree()
        self.assertEqual(path, Path.of("middle", "top"))
        self.assertEqual(len(t.samples), 1)

if __name__ == "__main__":
    main()
