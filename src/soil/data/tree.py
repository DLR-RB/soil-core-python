
from .path import Path


class Tree[T]:
    """
    A generic tree structure that can hold a value for each tree node.
    """

    def __init__(self, value: T | None = None, children: dict[str, 'Tree[T]'] | None = None) -> None:
        self.value: T | None = value
        if children is None:
            self.children: dict[str, Tree[T]] = dict()
        else:
            self.children: dict[str, Tree[T]] = children

    def __str__(self) -> str:
        """
        Return a human-readable description of the tree.
        """
        lines: list[str] = list()
        if self.value is not None:
            lines.append("Value:")
            lines.append(f"  {self.value}")
        if self.children:
            lines.append("Children:")
            for name, child in self.children.items():
                lines.append(f"  {name}")
                childLines = str(child).split("\n")
                lines.extend(["    " + l for l in childLines])
        return "\n".join(lines)

    def __eq__(self, other: object) -> bool:
        """
        Compare two sample trees.
        """
        if not isinstance(other, Tree):
            return False
        if self.value != other.value: # pyright: ignore[reportUnknownMemberType]
            return False

        return self.children == other.children # pyright: ignore[reportUnknownMemberType]

    @property
    def isEmpty(self) -> bool:
        """ Indicate if the tree contains any values """
        if self.value is not None:
            return False
        for child in self.children.values():
            if not child.isEmpty:
                return False
        return True

    def containedTree(self) -> tuple[Path, 'Tree[T]']:
        """
        Find the first meaningful subtree.

        Traverses down chains of single-child nodes until a node
        containing a value or multiple children is encountered.

        Returns
        -------
        Tuple[Path, Tree[T]]
            The path to the subtree and the subtree itself.
        """
        path = Path()
        current: Tree[T] = self

        while current.value is None and len(current.children) == 1:
            name, child = next(iter(current.children.items()))
            path.append(name)
            current = child

        return path, current

    def containedTreeAtPath(self, path: Path) -> tuple[Path, 'Tree[T]']:
        """
        Find the first meaningful subtree, and combine it with a given path.

        Traverses down chains of single-child nodes until a node
        containing samples or multiple children is encountered.

        Returns
        -------
        Tuple[Path, SampleTree]
            The full path to the subtree and the subtree itself.
        """
        subPath, tree = self.containedTree()
        return path.appending(subPath), tree

    def existingNode(self, path: Path) -> 'Tree[T] | None':
        """
        Get a node for a path below the current node, if it exists.

        This function is used for read and delete operations, and does not create any new nodes.
        - Parameter path: The path to select within the tree.
        - Returns: The node at the path, if it exists.
        """
        current: Tree[T] = self
        for name in path:
            child = current.existingChild(name)
            if child is None:
                return None
            current = child
        return current

    def existingChild(self, name: str) -> 'Tree[T] | None':
        return self.children.get(name)

    def existingNodes(self, path: Path) -> list['Tree[T]']:
        """
        Get all existing nodes in the tree on the way to a node corresponding to a path.
        - Note: Includes this node as the first element of the result
        - Parameter path: The path to the node.
        - Returns: All existing nodes along the path.
        """
        result: list[Tree[T]] = [self]
        last = self
        for component in path:
            child = last.existingChild(component)
            if child is None:
                break
            result.append(child)
            last = child
        return result

    def findOrCreateNode(self, path: Path) -> 'Tree[T]':
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

    def createChild(self, name: str) -> 'Tree[T]':
        child: Tree[T] = Tree()
        self.children[name] = child
        return child

    def add(self, child: 'Tree[T]', name: str) -> None:
        self.children[name] = child

    def child(self, name: str) -> 'Tree[T]':
        """
        Select a child of this node with a given name.

        The child will be created, if it doesn't exist.
        This function is used for write operations.
        - Parameter name: The name of the child.
        - Returns: The node of the child.
        """
        child: Tree[T] | None = self.existingChild(name)
        if child is not None:
            return child
        child = Tree()
        self.children[name] = child
        return child

    def insert(self, value: T | None, path: Path) -> None:
        """
        Insert a value into the tree.
        - Parameter value: The value to add
        - Parameter path: The path within this tree where the samples are added.
        - Note: The value replaces an already existing value
        """
        self.findOrCreateNode(path).value = value

    def mergeAtPath(self, tree: 'Tree[T]', path: Path):
        """
        Insert a tree into this tree.
        - Parameter tree: The tree to add
        - Parameter path: The path within this tree where the tree is added.
        - Note: The samples are appended to existing samples without sorting.
        """
        self.findOrCreateNode(path).merge(tree)

    def merge(self, tree: 'Tree[T]') -> None:
        """
        Insert a tree into this tree.
        - Parameter tree: The tree to add
        - Note: The values in the new tree override existing values in this tree.
        """
        if tree.value is not None:
            self.value = tree.value
        for name, child in tree.children.items():
            node = self.child(name)
            node.merge(child)
