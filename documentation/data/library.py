from soil.data import SampleTree, SampleTreeConvertible, Value, ValueConvertible


class Book(ValueConvertible):
    """ An object which is convertible into a single value. """

    def __init__(self, isbn: str, title: str, author: str):
        self._isbn: str = isbn
        self._title: str = title
        self._author: str = author

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
        """ Convert the book into a single Value """
        # Format: "isbn|title|author"
        return Value(f"{self._isbn}|{self._title}|{self._author}")

    @classmethod
    def fromValue(cls, value: Value) -> "Book":
        """ Create a book from a single Value """
        raw = value.value
        if not isinstance(raw, str):
            raise ValueError("The value does not have the structure of a Book")

        parts = raw.split("|")
        if len(parts) != 3:
            raise ValueError("The value does not have the structure of a Book")

        isbn, title, author = parts
        return cls(isbn, title, author)


class Library(SampleTreeConvertible):
    """ A structured object which stores the books in a SampleTree. """

    def __init__(self, name: str):
        self._name: str = name
        self._books: SampleTree = SampleTree()
        self.history: SampleTree = SampleTree()
        self._visitor_count: Value | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def books(self) -> SampleTree:
        return self._books

    @property
    def visitor_count(self) -> Value | None:
        return self._visitor_count

    def add_book(self, book: Book):
        book_value = book.toValue()
        self._books.childWithValue(book.isbn, book_value)

    def set_visitor_count(self, value: Value):
        self._visitor_count = value
        self.history.childWithValue("visitor_count", value)

    def toTree(self) -> SampleTree:
        """ Convert the library into a SampleTree """
        tree = SampleTree()

        tree.childWithValue("name", Value(self._name))

        tree.add(self._books, "books")
        tree.add(self.history, "history")

        return tree

    @classmethod
    def fromTree(cls, tree: SampleTree) -> "Library":
        """ Create a library from a SampleTree """
        nameNode = tree.existingChild("name")
        booksNode = tree.existingChild("books")
        historyNode = tree.existingChild("history")

        if nameNode is None or booksNode is None or historyNode is None:
            raise ValueError("The tree does not have the structure of a Library")

        nameSample = nameNode.newestSample
        if nameSample is None:
            raise ValueError("The tree does not have the structure of a Library")

        name = str(nameSample.value.value)

        library = cls(name)
        library._books = booksNode
        library.history = historyNode

        visitorNode = historyNode.existingChild("visitor_count")
        if visitorNode is not None and visitorNode.newestSample is not None:
            library._visitor_count = visitorNode.newestSample.value

        return library

    def get_book(self, isbn: str) -> Book | None:
        bookNode = self._books.existingChild(isbn)
        if bookNode is None or bookNode.newestSample is None:
            return None
        return Book.fromValue(bookNode.newestSample.value)


def visualize(tree: SampleTree, indent: str = "") -> None:
    for cname, child in tree.children.items():
        sample = child.newestSample
        value = sample.value.value if sample is not None else "–"
        print(f"{indent}├─ {cname}: {value}")

        if len(child.samples) > 1:
            for s in child.samples:
                ts = s.timestamp.timeIntervalSince1970 if s.timestamp is not None else "?"
                marker = "  ← now" if s is child.newestSample else ""
                print(f"{indent}│  ├─ {s.value.value}  (t={ts}){marker}")

        visualize(child, indent + "│  ")


def main():
    library = Library("Münchner Stadtbibliothek")

    library.add_book(Book("978-3-16-148410-0", "Der Prozess", "Franz Kafka"))
    library.add_book(Book("978-3-499-13550-2", "Der Alchimist", "Paulo Coelho"))
    library.add_book(Book("978-3-15-009958-4", "Faust I", "Johann W. Goethe"))

    library.set_visitor_count(Value(1200))
    library.set_visitor_count(Value(1350))

    tree = library.toTree()
    print("=== toTree() ===")
    visualize(tree)

    restored = Library.fromTree(tree)
    print("\n=== fromTree() ===")
    print(f"name          = {restored.name}")
    print(f"visitor_count = {restored.visitor_count}")

    book = restored.get_book("978-3-16-148410-0")
    print(f"book          = {book.title} von {book.author} ({book.isbn})")

    assert restored.name == library.name

    visitors = restored.visitor_count
    assert visitors is not None and visitors.value is not None

    assert book is not None
    assert book.title == "Der Prozess"
    assert book.author == "Franz Kafka"

    assert restored.history is tree.existingChild("history")


if __name__ == "__main__":
    main()