

from ..data import Path, SampleTree


class SubscriptionTree:
    """
    A class to manage a single subscription.

    The data is organized in a tree of nodes, where each node stores information
    about inclusions and exclusions.

    It's possible for multiple inclusions and exclusions to be specified for the
    same path, e.g. ``include(depth=3)``, ``exclude(depth=2)``,
    ``include(depth=1)``.

    The rules are stored with the lowest depths first, since lower depths take
    precedence.
    """

    def __init__(self):
        """
        Create a new subscription tree.
        """

        #: The nodes below this node, indexed by their name
        self.children: dict[str, SubscriptionTree] = {}

        #: The inclusion rules for the node, sorted by smallest first
        self._inclusions: list[int | None] = []

        #: The exclusion rules for the node, sorted by smallest first
        self._exclusions: list[int | None] = []

    @property
    def hasRules(self) -> bool:
        """Indicate if any rules are present."""
        return bool(self._inclusions or self._exclusions)

    @property
    def numberOfRules(self) -> int:
        """The number of rules at this node."""
        return len(self._inclusions) + len(self._exclusions)

    @property
    def totalNumberOfRules(self) -> int:
        """The total number of rules for all nodes in this tree."""
        return self.numberOfRules + sum(
            child.totalNumberOfRules
            for child in self.children.values()
        )

    @property
    def hasSubscriptionRulesInTree(self) -> bool:
        """Indicate if there is any rule registered for the subscription."""
        if self.hasRules:
            return True

        return any(
            child.hasSubscriptionRulesInTree
            for child in self.children.values()
        )

    @property
    def isEmpty(self) -> bool:
        """
        Indicate if the node does not contain a subscription or children.

        Note:
            This function does not check if child nodes are empty.
        """
        return not self.hasRules and not self.children

    @property
    def numberOfNodes(self) -> int:
        """The total number of nodes contained in this tree."""
        return 1 + sum(
            child.numberOfNodes
            for child in self.children.values()
        )

    # MARK: - Root Interface

    def include(
        self,
        path: Path,
        depth: int | None,
    ):
        """
        Include a path in the subscription.

        Args:
            path: The path to include.
            depth: The depth of the inclusion (``None`` indicates the full
                sub-tree).
        """
        self.findOrCreateNode(path).includeDepth(depth)

    def exclude(
        self,
        path: Path,
        depth: int | None,
    ):
        """
        Exclude a path from the subscription.

        Args:
            path: The path to exclude.
            depth: The depth of the exclusion (``None`` indicates the full
                sub-tree).
        """
        self.findOrCreateNode(path).excludeDepth(depth)

    def deleteRules(
        self,
        path: Path,
        depth: int | None,
    ):
        """
        Delete subscription rules at a path with a given depth.

        This function also deletes all empty nodes at the path after the rules
        are removed.

        Args:
            path: The path for which to delete rules.
            depth: The depth of the deletion.
        """
        nodes = self.existingNodes(path)

        if len(nodes) != len(path) + 1:
            # The node of the path does not exist,
            # so there are no rules to delete
            return

        # Select the node of the exact path
        node = nodes[len(path)]

        # Delete the rules at the node
        node.deleteRulesDepth(depth)

        # Traverse to the root and delete empty nodes
        index = len(path) - 1

        while node.isEmpty and index >= 0:
            # Go the higher node
            node = nodes[index]

            # Get the path component of the child
            component = path[index]

            # Delete the empty node
            node.children.pop(component, None)

            # Move up to the next node
            index -= 1

    def deleteAllRules(self):
        """
        Delete all rules in the tree.
        """
        self.deleteRules(Path(), None)

    # MARK: - Subscription Modifications

    def includeDepth(
        self,
        depth: int | None,
    ):
        """
        Add an inclusion with a depth.

        Adding an inclusion will remove an existing exclusion of the same
        depth.
        """
        # We only insert an inclusion if it doesn't already exist
        if depth in self._inclusions:
            return

        # Remove a corresponding exclusion, if it exists
        if depth in self._exclusions:
            self._exclusions.remove(depth)

        self._insertSorted(self._inclusions, depth)

    def excludeDepth(
        self,
        depth: int | None,
    ):
        """
        Add an exclusion with a depth.

        Adding an exclusion will remove an existing inclusion of the same
        depth.
        """
        # We only insert an exclusion if it doesn't already exist
        if depth in self._exclusions:
            return

        # Remove a corresponding inclusion, if it exists
        if depth in self._inclusions:
            self._inclusions.remove(depth)

        self._insertSorted(self._exclusions, depth)

    def deleteRulesDepth(
        self,
        depth: int | None,
    ):
        """
        Delete all rules in this tree, up to a given depth.

        Recurses into child nodes to remove all data.

        Args:
            depth: The depth of the deletion.
        """
        self._inclusions.clear()
        self._exclusions.clear()

        # Stop recursing if depth is reached
        if depth == 0:
            return

        newDepth = None if depth is None else depth - 1

        remaining: dict[str, SubscriptionTree] = {}

        for name, child in self.children.items():
            child.deleteRulesDepth(newDepth)

            if not child.isEmpty:
                remaining[name] = child

        self.children = remaining

    # MARK: - Helpers

    def child(self, name: str) -> 'SubscriptionTree':
        """
        Select a child of this node with a given name.

        The child will be created, if it doesn't exist.
        This function is used for write operations.
        - Parameter name: The name of the child.
        - Returns: The node of the child.
        """
        child = self.children.get(name)
        if child is not None:
            return child
        child = SubscriptionTree()
        self.children[name] = child
        return child

    def findOrCreateNode(self, path: Path) -> 'SubscriptionTree':
        """
        Find an existing node, or create it in the tree.

        Used when inserting a subscription or exclusion.
        - Parameter path: The path to the node.
        - Returns: The final node corresponding to the path
        """
        node = self
        for component in path:
            node = node.child(component)
        return node

    def existingChild(self, name: str) -> 'SubscriptionTree | None':
        return self.children.get(name)

    def existingNodes(self, path: Path) -> list['SubscriptionTree']:
        """
        Get all existing nodes in the tree on the way to a node corresponding to a path.
        - Note: Includes this node as the first element of the result
        - Parameter path: The path to the node.
        - Returns: All existing nodes along the path.
        """
        result: list[SubscriptionTree] = [self]
        last: SubscriptionTree = self
        for component in path:
            child = last.existingChild(component)
            if child is None:
                break
            result.append(child)
            last = child
        return result

    @staticmethod
    def _insertSorted(
        values: list[int | None],
        value: int | None,
    ):
        """
        Insert a depth into a sorted list.

        ``None`` is treated as larger than any integer.
        """
        def isInOrder(lhs: int | None, rhs: int | None) -> bool:
            if lhs is None:
                return False
            if rhs is None:
                return True
            return lhs <  rhs

        index = 0
        while index < len(values) and isInOrder(values[index], value):
            index += 1

        values.insert(index, value)

    # MARK: - Subscription Queries

    def reduce(
        self,
        tree: SampleTree,
        path: Path,
    ) -> SampleTree | None:
        """
        Use the subscriptions to remove all excluded parts of a tree.

        Args:
            tree: The original tree to strip.
            path: The path of the tree in relation to the subscription tree.

        Returns:
            The reduced tree, if any inclusion rules match.
        """
        nodes = self._allNodes(path)

        # Note: The path nodes always include at least the root node
        return nodes[-1].reduceNode(tree, parents=nodes)

    def _allNodes(
        self,
        path: Path,
    ) -> list['SubscriptionTree']:
        """
        Get all nodes along a path, including dummy nodes if needed.

        Args:
            path: The path for which to collect the nodes.

        Note:
            A single dummy node is added multiple times if needed,
            so the nodes must not be modified while used.
        """
        nodes = self.existingNodes(path)

        # We always include the root node, so we expect one more node than
        # the number of path elements
        missingCount = len(path) + 1 - len(nodes)
        if missingCount == 0:
            return nodes

        dummy = SubscriptionTree()
        return nodes + [dummy] * missingCount

    def reduceNode(
        self,
        tree: SampleTree,
        parents: list['SubscriptionTree'] | None = None,
    ) -> SampleTree | None:
        """
        Use the subscriptions to remove all excluded parts of a tree.

        Args:
            tree: The original tree to strip.
            parents: The nodes above this node in the subscription tree.

        Returns:
            The reduced tree, if any samples or children remain after
            reduction.

        The samples of the tree root are included in the result,
        if either the current node has a suitable rule, or if a parent node
        matches. The children are included if their subscriptions match,
        which also consider the rules of this node.
        """
        if parents is None:
            parents = []

        childrenAreSubscribed = self._isSubscribed(
            parentNodes=parents,
            depth=1,
        )

        childParents = parents + [self]

        reduced: dict[str, SampleTree] = {}

        for childName, childTree in tree.children.items():
            subscriptionChild = self.children.get(childName)

            if subscriptionChild is None:
                # No rules for child, so use only the ones of the current node
                if childrenAreSubscribed:
                    reduced[childName] = childTree
                continue

            reducedChild = subscriptionChild.reduceNode(
                childTree,
                parents=childParents,
            )

            if reducedChild is not None:
                reduced[childName] = reducedChild

        samples = (
            tree.samples
            if self._isSubscribed(parentNodes=parents, depth=0)
            else []
        )

        if not samples and not reduced:
            return None

        return SampleTree(
            samples=samples,
            children=reduced,
        )

    def _isSubscribed(
        self,
        parentNodes: list['SubscriptionTree'],
        depth: int,
    ) -> bool:
        """
        Check if the current node or parent nodes have a matching
        subscription for a given depth below this node.

        Args:
            parentNodes: The nodes above this node in the subscription tree.
            depth: The depth below this node to check.

        Returns:
            ``True`` if the depth is included in the subscription.

        If no applicable rule exists for the current node, then the parent
        node is checked. This process repeats until the tree root is reached.
        """
        included = self._isIncluded(depth)
        if included is not None:
            return included

        if not parentNodes:
            # No parent nodes, so not included
            return False

        parent = parentNodes[-1]
        return parent._isSubscribed(
            parentNodes[:-1],
            depth + 1,
        )

    def isSubscribed(
        self,
        path: Path,
    ) -> bool:
        """
        Check if a path is covered by the inclusions in the tree.

        The function first finds all existing nodes along the path,
        and then traverses them from the bottom node to the root.
        If a node in the subscription tree has a matching rule
        (based on the relative depth), then the inclusion or exclusion is
        returned. If the full path is traversed to the top, then the path
        is not included.

        Args:
            path: The path to query subscriptions for.

        Returns:
            ``True`` if the path is included by the subscription.
        """
        # Traverse the tree to get the nodes along the path,
        # so that we can move towards the root
        nodes = self.existingNodes(path)

        # We start at the lowest existing node containing any subscriptions
        # or inclusions, and work our way up to the root
        level = len(nodes) - 1

        while level >= 0:
            node = nodes[level]

            # The relative level describes how many levels the full path is
            # below the current node. This number can directly be compared
            # to the depth of subscriptions and inclusions to check if they
            # are relevant.
            relativePathLevel = len(path) - level

            included = node._isIncluded(relativePathLevel)
            if included is not None:
                return included

            # Advance to the next higher node
            level -= 1

        # If we reach past the root node then the path is not contained in
        # the subscription
        return False

    _MISSING = object()

    def _isIncluded(
        self,
        depth: int,
    ) -> bool | None:
        """
        Check if the subscription of a path is triggered (included or
        excluded) by the rules at this node.

        Args:
            depth: The depth of the path below this node.

        Returns:
            ``True`` if the path is included,
            ``False`` if the path is excluded,
            ``None`` if no rule applies.
        """
        # Find the smallest depth that includes the given depth.
        # Smaller depths take precedence, so we can ignore the rest,
        # as well as all rules that don't apply.
        # Note: ``None`` indicates an unlimited depth and is applicable
        # to every depth. It must not be confused with the absence of a rule.
        def isApplicable(rule: int | None) -> bool:
            return rule is None or rule >= depth

        inclusions = [d for d in self._inclusions if isApplicable(d)]
        exclusions = [d for d in self._exclusions if isApplicable(d)]

        if not inclusions:
            # No inclusion, so it's excluded if any exclusion rule applies
            return False if exclusions else None

        if not exclusions:
            # No exclusion, so it's included
            return True

        # Both inclusion and exclusion rules apply.
        # The lower depth wins, where ``None`` (unlimited) is treated as
        # larger than any integer.
        # Equality is prevented during insertion of rules.
        def asRank(rule: int | None) -> float:
            return float("inf") if rule is None else rule

        return asRank(inclusions[0]) < asRank(exclusions[0])

    # MARK: - String Conversion

    def __str__(self) -> str:
        return (
            f"Tree({self.numberOfNodes} nodes, "
            f"{self.totalNumberOfRules} rules)"
        )

    def described(
        self,
        indent: str,
    ) -> list[str]:
        lines: list[str] = []

        if self.hasRules:
            lines.append("rules")

            for depth in self._inclusions:
                lines.append(f"- include({depth})")

            for depth in self._exclusions:
                lines.append(f"- exclude({depth})")

        if self.children:
            lines.append("children")

            for name, child in sorted(self.children.items()):
                lines.append(indent + name)
                lines.extend(
                    indent + indent + line
                    for line in child.described(indent)
                )

        return lines
