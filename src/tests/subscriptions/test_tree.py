import unittest

from soil.data import Path, SampleTree
from soil.data.sample import Sample
from soil.data.value import Value
from soil.subscriptions.tree import SubscriptionTree


class testSubscriptionTree(unittest.TestCase):

    def test_HasRules(self):
        st = SubscriptionTree()
        self.assertFalse(st.hasRules)

        st = SubscriptionTree()
        st.include(Path(), 1)
        self.assertTrue(st.hasRules)


    def test_NumberOfRules(self):
        st = SubscriptionTree()
        self.assertEqual(st.numberOfRules, 0)

        st = SubscriptionTree()
        st.include(Path(), 1)
        st.exclude(Path(), 2)
        self.assertEqual(st.numberOfRules, 2)


    def test_TotalNumberOfRules(self):
        st = SubscriptionTree()
        st.include(Path(), 1)
        self.assertEqual(st.totalNumberOfRules, 1)


    def test_HasSubscriptionRulesInTree(self):
        st = SubscriptionTree()
        st.include(Path(), 1)
        self.assertTrue(st.hasSubscriptionRulesInTree)

        st = SubscriptionTree()
        st.include(Path.of("a"), 1)
        self.assertTrue(st.hasSubscriptionRulesInTree)

        st = SubscriptionTree()
        self.assertFalse(st.hasSubscriptionRulesInTree)


    def test_IsEmpty(self):
        st = SubscriptionTree()
        self.assertTrue(st.isEmpty)

        st = SubscriptionTree()
        st.include(Path(), 1)
        self.assertFalse(st.isEmpty)

        st = SubscriptionTree()
        st.include(Path.of("a"), 1)
        self.assertFalse(st.isEmpty)


    def test_NumberOfNodes(self):
        st = SubscriptionTree()
        self.assertEqual(st.numberOfNodes, 1)

        st = SubscriptionTree()
        st.include(Path.of("a", "b"), 1)
        self.assertEqual(st.numberOfNodes, 3)



class TestIncludeExclude(unittest.TestCase):

    def test_Include(self):
        st = SubscriptionTree()
        st.include(Path(), 2)
        self.assertIn(2, st._inclusions)

        st = SubscriptionTree()
        st.include(Path.of("a", "b"), 3)
        node = st.children["a"].children["b"]
        self.assertIn(3, node._inclusions)


    def test_Exclude(self):
        st = SubscriptionTree()
        st.exclude(Path(), 2)
        self.assertIn(2, st._exclusions)

        st = SubscriptionTree()
        st.exclude(Path.of("x"), 1)
        self.assertIn(1, st.children["x"]._exclusions)


    def test_IncludeDepth(self):
        st = SubscriptionTree()
        st.includeDepth(2)
        self.assertEqual(st._inclusions, [2])

        st = SubscriptionTree()
        st.includeDepth(2)
        st.includeDepth(2)
        self.assertEqual(st._inclusions, [2])

        st = SubscriptionTree()
        st.excludeDepth(3)
        st.includeDepth(3)
        self.assertEqual(st._inclusions, [3])
        self.assertEqual(st._exclusions, [])

        st = SubscriptionTree()
        st.includeDepth(3)
        st.includeDepth(1)
        st.includeDepth(2)
        self.assertEqual(st._inclusions, [1, 2, 3])      

        st = SubscriptionTree()
        st.includeDepth(None)
        st.includeDepth(1)
        self.assertEqual(st._inclusions, [1, None])


    def test_ExcludeDepth(self):
        st = SubscriptionTree()
        st.excludeDepth(1)
        self.assertEqual(st._exclusions, [1])

        st = SubscriptionTree()
        st.excludeDepth(1)
        st.excludeDepth(1)
        self.assertEqual(st._exclusions, [1])

        st = SubscriptionTree()
        st.includeDepth(5)
        st.excludeDepth(5)
        self.assertEqual(st._exclusions, [5])
        self.assertEqual(st._inclusions, [])

class TestDeleteRules(unittest.TestCase):

    def test_DelteRules(self):
        st = SubscriptionTree()
        st.include(Path.of("a"), 2)
        st.deleteRules(Path.of("a"), 2)
        self.assertNotIn("a", st.children)

        st = SubscriptionTree()
        st.include(Path.of("a"), 1)
        st.include(Path.of("a"), 2)
        st.deleteRules(Path.of("a"), None)
        self.assertNotIn("a", st.children)

        st = SubscriptionTree()
        st.include(Path.of("a"), 1)
        st.deleteRules(Path.of("x", "y"), 1)
        self.assertIn(1, st.children["a"]._inclusions)


    def test_DeleteAllRules(self):
        st = SubscriptionTree()
        st.include(Path(), 1)
        st.include(Path.of("a"), 2)
        st.deleteAllRules()
        self.assertEqual(st._inclusions, [])
        self.assertEqual(st.children, {})


    def test_DeleteRulesDepth(self):
        st = SubscriptionTree()
        st.includeDepth(1)
        st.excludeDepth(2)
        st.deleteRulesDepth(None)
        self.assertEqual(st._inclusions, [])
        self.assertEqual(st._exclusions, [])

        st = SubscriptionTree()
        st.includeDepth(1)
        child = SubscriptionTree()
        child.includeDepth(5)
        st.children["x"] = child
        st.deleteRulesDepth(0)
        self.assertEqual(st._inclusions, [])
        self.assertEqual(child._inclusions, [5])

        st = SubscriptionTree()
        st.includeDepth(1)
        child = SubscriptionTree()
        child.includeDepth(5)
        st.children["x"] = child
        st.deleteRulesDepth(None)
        self.assertEqual(st._inclusions, [])
        self.assertEqual(child._inclusions, [])



class TestSubscriptionQueries(unittest.TestCase):

    def _tree(self) -> SampleTree:
        return SampleTree(samples=[Sample(Value(1))], children={
            "a": SampleTree([Sample(Value(2))]),
            "b": SampleTree([Sample(Value(3))]),
        })


    def test_IsSubscribed_NoRules(self):
        st = SubscriptionTree()
        self.assertFalse(st.isSubscribed(Path.of("a")))

    def test_IsSubscribed_DepthBoundary(self):
        st = SubscriptionTree()
        st.include(Path(), 1)
        self.assertTrue(st.isSubscribed(Path()))
        self.assertTrue(st.isSubscribed(Path.of("a")))
        self.assertFalse(st.isSubscribed(Path.of("a", "b")))

    def test_IsSubscribed_LowerDepthWins(self):
        st = SubscriptionTree()
        st.include(Path(), 2)
        st.exclude(Path(), 1)
        self.assertFalse(st.isSubscribed(Path.of("a")))
        self.assertTrue(st.isSubscribed(Path.of("a", "b")))

    def test_IsSubscribed_ExcludeFullSubtree(self):
        st = SubscriptionTree()
        st.include(Path(), 2)
        st.exclude(Path.of("a"), None)
        self.assertTrue(st.isSubscribed(Path()))
        self.assertFalse(st.isSubscribed(Path.of("a")))
        self.assertFalse(st.isSubscribed(Path.of("a", "b")))

    def test_IsSubscribed_FullTreeInclusion(self): # BUG?!
        st = SubscriptionTree()
        st.include(Path(), None)
        self.assertTrue(st.isSubscribed(Path.of("a", "b")))




class TestHelper(unittest.TestCase):

    def test_Str(self):
        st = SubscriptionTree()
        st.includeDepth(2)
        st.excludeDepth(3)
        lines = st.described("  ")
        self.assertEqual(lines[0], "rules")
        self.assertIn("- include(2)", lines)
        self.assertIn("- exclude(3)", lines)



    def test_Described(self):
        st = SubscriptionTree()
        self.assertEqual(st.described("  "), [])

        st = SubscriptionTree()
        st.includeDepth(2)
        st.excludeDepth(3)
        lines = st.described("  ")
        self.assertEqual(lines[0], "rules")
        self.assertIn("- include(2)", lines)
        self.assertIn("- exclude(3)", lines)

        st = SubscriptionTree()
        st.include(Path.of("a"), 1)
        lines = st.described("  ")
        self.assertIn("children", lines)
        self.assertIn("  a", lines)