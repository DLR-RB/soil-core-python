from soil.data import SampleTree, SampleTreeConvertible, Value, ValueConvertible


class Book(ValueConvertible):
    """
    A book with ISBN, title, and author.

    This demonstrates `ValueConvertible` for a simple object that serializes
    to a single string value (pipe-delimited format).
    """

    def __init__(self, isbn: str, title: str, author: str):
        self._isbn = isbn
        self._title = title
        self._author = author

    @property
    def isbn(self) -> str:
        return self._isbn

    @property
    def title(self) -> str:
        return self._title

    @property
    def author(self) -> str:
        return self._author

    def toValue(self) -> Value:
        """Convert the book into a single string Value (pipe-delimited format)."""
        return Value(f"{self._isbn}|{self._title}|{self._author}")

    @classmethod
    def fromValue(cls, value: Value) -> "Book":
        """Create a Book from a single string Value."""
        raw = value.value
        if not isinstance(raw, str):
            raise ValueError("Value must be a string in format 'isbn|title|author'")

        parts = raw.split("|")
        if len(parts) != 3:
            raise ValueError(f"Expected 3 parts (isbn|title|author), got {len(parts)}")

        isbn, title, author = parts
        return cls(isbn, title, author)


class Library(SampleTreeConvertible):
    """
    A library that manages multiple books.

    This demonstrates:
    - `SampleTreeConvertible` for hierarchical data
    - Books stored in a SampleTree keyed by ISBN
    - Visitor count history tracking
    - Complete serialization/deserialization round-trips
    """

    def __init__(self, name: str):
        self._name = name
        self._books = SampleTree()
        self._history = SampleTree()

    @property
    def name(self) -> str:
        return self._name

    @property
    def books(self) -> SampleTree:
        return self._books

    def add_book(self, book: Book) -> None:
        """Add a book to the library."""
        book_value = book.toValue()
        self._books.childWithValue(book.isbn, book_value)

    def remove_book(self, isbn: str) -> bool:
        """Remove a book from the library by ISBN. Returns True if removed."""
        book_node = self._books.existingChild(isbn)
        if book_node is None:
            return False
        # delete() requires end and depth parameters; delete all samples at this path
        self._books.delete(isbn, end=None, depth=0)
        return True

    def get_book(self, isbn: str) -> Book | None:
        """Retrieve a book by ISBN."""
        book_node = self._books.existingChild(isbn)
        if book_node is None or book_node.newestSample is None:
            return None
        return Book.fromValue(book_node.newestSample.value)

    def book_count(self) -> int:
        """Return the total number of books in the library."""
        return len(self._books.children)

    def record_visitor_count(self, count: int) -> None:
        """Record a visitor count (demonstrates history with multiple samples)."""
        self._history.childWithValue("visitors", Value(count))

    def get_latest_visitor_count(self) -> int | None:
        """Get the most recent visitor count."""
        node = self._history.existingChild("visitors")
        if node is None or node.newestSample is None:
            return None
        raw = node.newestSample.value
        if raw is None:
            return None
        return int(raw.value)

    def toTree(self) -> SampleTree:
        """Convert the library to a SampleTree."""
        tree = SampleTree()

        # Store library name
        tree.childWithValue("name", Value(self._name))

        # Add books tree
        tree.add(self._books, "books")

        # Add history
        tree.add(self._history, "history")

        return tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "Library":
        """Reconstruct a Library from a SampleTree."""
        # Extract name
        name_node = tree.existingChild("name")
        if name_node is None or name_node.newestSample is None:
            raise ValueError("Tree missing 'name' in root")
        name = str(name_node.newestSample.value.value)

        # Extract books and history
        books_node = tree.existingChild("books")
        history_node = tree.existingChild("history")

        if books_node is None:
            raise ValueError("Tree missing 'books' node")

        # Create library with extracted nodes
        library = cls(name)
        library._books = books_node
        library._history = history_node if history_node is not None else SampleTree()

        return library


def visualize(tree: SampleTree, indent: str = "", max_depth: int = -1, current_depth: int = 0) -> None:
    """
    Display a tree structure with proper formatting.

    Shows:
    - Map values with indented key-value pairs
    - List values with bracket notation
    - Multiple samples with timestamps
    - Current value markers
    """
    if max_depth >= 0 and current_depth > max_depth:
        return

    for child_name, child in tree.children.items():
        sample = child.newestSample
        value = sample.value if sample is not None else None
        value_display = _format_value(value, indent)

        print(f"{indent}|- {child_name}: {value_display}")

        # Show multiple samples if present
        if len(child.samples) > 1:
            for s in child.samples:
                ts = s.timestamp.timeIntervalSince1970 if s.timestamp else "?"
                marker = "  <- now" if s is child.newestSample else ""
                val = _format_value(s.value, indent + "|  ")
                print(f"{indent}|  |- {val}  (t={ts}){marker}")

        # Recursively show children
        if child.children:
            visualize(child, indent + "|  ", max_depth, current_depth + 1)


def _format_value(value: Value | None, indent: str = "") -> str:
    """Format a Value for display."""
    if value is None:
        return "-"

    raw = value.value

    if isinstance(raw, dict):
        # Map: show first few keys
        if len(raw) == 0:
            return "{}"
        keys = list(raw.keys())[:3]
        if len(raw) > 3:
            return f"{{{', '.join(keys)}...}}"
        return f"{{{', '.join(keys)}}}"
    elif isinstance(raw, list):
        # List: show count
        if len(raw) == 0:
            return "[]"
        return f"[{len(raw)} items]"
    else:
        # Primitive: show raw value
        return str(raw)


def main():
    """Demonstrate the Library class."""
    print("=" * 60)
    print("Library Example")
    print("=" * 60)

    # Create a library
    library = Library("Munich City Library")

    # Add books
    print("\nAdding books...")
    library.add_book(Book("978-3-16-148410-0", "Der Prozess", "Franz Kafka"))
    library.add_book(Book("978-3-499-13550-2", "Der Alchimist", "Paulo Coelho"))
    library.add_book(Book("978-3-15-009958-4", "Faust I", "Johann W. Goethe"))
    library.add_book(Book("978-0-14-028329-7", "The Great Gatsby", "F. Scott Fitzgerald"))

    print(f"  Added {library.book_count()} books")

    # Record visitor history
    print("\nRecording visitor counts...")
    library.record_visitor_count(1200)
    library.record_visitor_count(1350)
    library.record_visitor_count(1520)

    print(f"  Latest visitors: {library.get_latest_visitor_count()}")

    # Serialize to tree
    print("\n" + "=" * 60)
    print("=== toTree() - Serialized Library ===")
    tree = library.toTree()
    visualize(tree, max_depth=2)

    # Deserialize from tree
    print("\n" + "=" * 60)
    print("=== fromTree() - Restored Library ===")
    restored = Library.fromTree(tree)

    print(f"Name:        {restored.name}")
    print(f"Book count:  {restored.book_count()}")
    print(f"Latest visitors: {restored.get_latest_visitor_count()}")

    # Show some books
    print("\nBooks in library:")
    for isbn in ["978-3-16-148410-0", "978-0-14-028329-7"]:
        book = restored.get_book(isbn)
        if book:
            print(f"  - {book.title} by {book.author} (ISBN: {book.isbn})")

if __name__ == "__main__":
    main()