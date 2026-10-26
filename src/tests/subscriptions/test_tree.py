<<<<<<< src/tests/subscriptions/test_tree.py
from unittest import TestCase

from soil.data import Path, SampleTree, Value
from soil.subscriptions import SubscriptionTree

class SubscriptionTreeTest(TestCase):
    # MARK: - Registration

    def test_root_inclusion_with_unlimited_depth_covers_all_paths(self):
        """Regression: an inclusion with unlimited depth (``None``) must be
        honored, and must not be confused with the absence of a rule.

        The old implementation used ``None`` both as the stored value for
        unlimited depths and as the "no rule found" sentinel, which made
        every unlimited inclusion invisible.
        """
        tree = SubscriptionTree()
        tree.include(Path(), depth=None)

        assert tree.isSubscribed(Path())
        assert tree.isSubscribed(Path.of("a"))
        assert tree.isSubscribed(Path.of("a", "b", "c"))


    def test_nested_inclusion_only_covers_the_subtree(self):
        tree = SubscriptionTree()
        tree.include(Path.of("a", "b"), depth=None)

        assert tree.isSubscribed(Path.of("a", "b"))
        assert tree.isSubscribed(Path.of("a", "b", "c"))
        assert not tree.isSubscribed(Path.of("a"))
        assert not tree.isSubscribed(Path.of("b"))


    def test_inclusion_with_integer_depth_limits_reach(self):
        tree = SubscriptionTree()
        tree.include(Path(), depth=2)

        assert tree.isSubscribed(Path.of("a"))
        assert tree.isSubscribed(Path.of("a", "b"))
        assert not tree.isSubscribed(Path.of("a", "b", "c"))


    # MARK: - Precedence

    def test_exclusion_overrides_inclusion(self):
        tree = SubscriptionTree()
        tree.include(Path(), depth=None)
        tree.exclude(Path.of("a"), depth=None)

        assert tree.isSubscribed(Path.of("a", "b")) is False
        assert tree.isSubscribed(Path.of("b"))


    def test_mixed_unlimited_inclusion_and_integer_exclusion(self):
        """Regression: the lower depth wins, where ``None`` (unlimited) counts
        as larger than any integer. The old implementation compared
        ``None`` against integers directly, raising a ``TypeError``."""
        tree = SubscriptionTree()
        tree.include(Path(), depth=None)
        tree.exclude(Path(), depth=2)

        # exclude(2) is the lower depth and wins within its reach
        assert not tree.isSubscribed(Path.of("a", "b"))
        # beyond the exclusion's reach the unlimited inclusion applies
        assert tree.isSubscribed(Path.of("a", "b", "c"))


    def test_mixed_integer_inclusion_and_unlimited_exclusion(self):
        tree = SubscriptionTree()
        tree.include(Path(), depth=1)
        tree.exclude(Path(), depth=None)

        # include(1) is the lower depth and wins within its reach
        assert tree.isSubscribed(Path.of("a"))
        # beyond the inclusion's reach the unlimited exclusion applies
        assert not tree.isSubscribed(Path.of("a", "b"))


    # MARK: - Deletion

    def test_delete_rules_removes_inclusions(self):
        tree = SubscriptionTree()
        tree.include(Path(), depth=None)

        tree.deleteRules(Path(), None)

        assert not tree.isSubscribed(Path.of("a"))
        assert tree.totalNumberOfRules == 0


    # MARK: - Reduction

    def test_reduce_returns_subscribed_samples(self):
        """Regression: a push to a path covered by an unlimited inclusion
        must not be silently dropped."""
        tree = SubscriptionTree()
        tree.include(Path(), depth=None)

        reduced = tree.reduce(SampleTree.ofValue(Value(42)), Path.of("model", "x"))

        assert reduced is not None
        assert reduced.newestSample is not None
        assert reduced.newestSample.value.value == 42


    def test_reduce_returns_none_without_matching_rules(self):
        tree = SubscriptionTree()

        reduced = tree.reduce(SampleTree.ofValue(Value(1)), Path.of("a"))

        assert reduced is None


    def test_reduce_drops_unsubscribed_children(self):
        tree = SubscriptionTree()
        tree.include(Path.of("a"), depth=None)

        data = SampleTree.create(children={
            "a": SampleTree.ofValue(Value(1)),
            "b": SampleTree.ofValue(Value(2)),
        })

        reduced = tree.reduce(data, Path())

        assert reduced is not None
        assert "a" in reduced.children
        assert "b" not in reduced.children


    def test_reduce_honors_deeply_nested_inclusion(self):
        """The pattern used by the KSAT adapter: one inclusion per command path."""
        tree = SubscriptionTree()
        tree.include(Path.of("system", "fetchSystems"), depth=None)

        reduced = tree.reduce(
            SampleTree.ofValue(Value(7)),
            Path.of("system", "fetchSystems"),
        )

        assert reduced is not None
        assert reduced.newestSample.value.value == 7
=======
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


    def test_print_logger_formats_multiple_arguments():

        logger = PrintLogger()
    from soil.data import Path
        # Must not raise: two placeholders, two positional arguments
    from soil.logging.level import LogLevel
        logger.log(LogLevel.ERROR, "Type mismatch: '{}' does not fit type {}", "bogus", "STRING")


>>>>>>> src/tests/subscriptions/test_tree.py
