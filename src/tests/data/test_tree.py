from unittest import TestCase

from soil.data import ImmutableSampleTree, Path, Tree, Value


class TreeTests(TestCase):

    def testContainedTree(self):
        top = ImmutableSampleTree.ofValue(Value(123))
        middle = ImmutableSampleTree(None, {"top": top})
        root = ImmutableSampleTree(None, {"middle": middle})

        path, t = root.containedTree()
        self.assertEqual(path, Path.of("middle", "top"))
        self.assertEqual(len(t.samples), 1)



    def test_constructor(self):
        tree1 = Tree(value=Value(1))
        tree2 = Tree()

        self.assertEqual(tree1.value, Value(1))
        self.assertEqual(tree2.value, None)

        self.assertEqual(tree1.children and tree2.children, {})



    def test_isEmpty(self):
        tree1 = Tree(value=Value(1))
        tree2 = Tree()

        self.assertFalse(tree1.isEmpty)
        self.assertTrue(tree2.isEmpty)


    def testContainedTreeAtPath(self):
        top = ImmutableSampleTree.ofValue(Value(123))
        middle = ImmutableSampleTree(None, {"top": top})
        root = ImmutableSampleTree(None, {"middle": middle})

        path, tree = root.containedTree()

        self.assertEqual(tree.containedTreeAtPath(Path(["middle", "top"])), (path, top))


    def testExistingNode(self):
        root = Tree[int]()
        a   = root.createChild("a");   a.value = 1
        aa  = a.createChild("aa");    aa.value = 11
        b   = root.createChild("b");   b.value = 2
        ba  = b.createChild("ba");    ba.value = 21
        bb  = b.createChild("bb");    bb.value = 22

        self.assertEqual(root.existingNode(Path(["b", "bb"])), bb)
        self.assertEqual(root.existingNode(Path(["b", "bc"])), None)


    def testExistingChild(self):
        root = Tree[int]()
        a   = root.createChild("a");   a.value = 1

        self.assertEqual(root.existingChild("a"), a)
        self.assertEqual(root.existingChild("a").value, 1) # type: ignore

    def testExistingNodes(self):
        root = Tree[int]()
        a   = root.createChild("a");   a.value = 1
        aa  = a.createChild("aa");    aa.value = 11
        b   = root.createChild("b");   b.value = 2
        ba  = b.createChild("ba");    ba.value = 21
        bb  = b.createChild("bb");    bb.value = 22

        self.assertEqual(root.existingNodes(Path(["a", "aa"])), [root, a, aa])
        self.assertEqual(root.existingNodes(Path(["a", "b", "bb"])), [root, a])
        self.assertEqual(root.existingNodes(Path(["bb"])), [root])


    def testFindOrCreateNode(self):
        root = Tree[int]()
        a   = root.createChild("a");   a.value = 1
        aa  = a.createChild("aa");    aa.value = 11
        b   = root.createChild("b");   b.value = 2
        c = root.findOrCreateNode(Path(["c"]))
        bb_find = root.findOrCreateNode(Path(["a", "b", "bb"]))

        self.assertIs(c, root.existingChild("c"))
        self.assertIs(bb_find, root.existingChild("a").existingChild("b").existingChild("bb")) # type: ignore


    def testCreateChild(self):
        root = Tree[int]()
        root.createChild("new_child")

        self.assertTrue(root.existingChild("new_child"))


    def testAdd(self):
        root = Tree[int]()
        new_child = Tree[int](1)
        root.add(new_child, "new_child")

        self.assertTrue(root.existingChild("new_child"))


    def testChild(self):
        root = Tree[int]()
        root.add(Tree[int](1), "new_child_from_add")
        root.child("new_child_from_func")

        self.assertTrue(root.existingChild("new_child_from_add"))
        self.assertTrue(root.existingChild("new_child_from_func"))


    def testInsert(self):
        root = Tree[int]()
        a   = root.createChild("a");   a.value = 1
        aa  = a.createChild("aa");    aa.value = 11
        b   = root.createChild("b");  
        ba  = b.createChild("ba");    ba.value = 21
        bb  = b.createChild("bb");

        root.insert(21, Path(["b"]))
        root.insert(12, Path(["b", "bb"]))

        root.insert(1, Path(["a", "ab", "aba"]))

        aba = root.existingNode(Path(["a", "ab", "aba"]))

        self.assertEqual(b.value, 21)
        self.assertEqual(bb.value, 12)
        self.assertEqual(aba.value, 1) # type: ignore


    def testMerge(self):
        root = Tree[int]()
        branch = Tree[int](1)
        leaf = Tree[int](2)
        root.merge(branch)
        branch.merge(leaf)

        path, subtree = root.containedTree()

        self.assertEqual(path, Path())
        self.assertIs(subtree, root)

    def testMergeAtPath(self):
        root = Tree[int]()
        branch = Tree[int](1)
        leaf = Tree[int](2)

        root.mergeAtPath(branch, Path())
        root.mergeAtPath(leaf, Path("branch"))

        path, subtree = root.containedTree()

        self.assertEqual(path, Path())
        self.assertIs(subtree, root)






    







