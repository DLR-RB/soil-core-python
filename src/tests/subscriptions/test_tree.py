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