from unittest import TestCase

from requests import patch

from soil.data import Path, Value
from soil.data.type import ValueType
from soil.data.value import formatFloat



class testPath(TestCase):

    def test_path_creation(self):
        path = Path.of("sensor", "temperature")
        
        self.assertEqual(len(path), 2)
        self.assertEqual(path[0], "sensor")
        self.assertEqual(path[1], "temperature")
        self.assertFalse(path.isEmpty)

    def test_append_to_path(self):
        base_path = Path.of("house")
        full_path = base_path.appending("room1")
        
        self.assertEqual(full_path.size, 2)
        self.assertEqual(full_path, ['house', 'room1'])

    def test_appendElse(self):
        p = Path.of("a")
        result = p.appending(["b", "c"])

        self.assertEqual(list(result), ["a", "b", "c"])
        self.assertIsInstance(result, Path)


    def test_hasPrefix_smaller(self):
        p = Path.of("a")
        prefix = Path.of("a", "b")
        self.assertFalse(p.hasPrefix(prefix))

    def test_hasPrefix_bigger_false(self):
        p = Path.of("a", "x")
        prefix = Path.of("a", "b")
        self.assertFalse(p.hasPrefix(prefix))

    def test_hasPrefix_bigger_true(self):
        p = Path.of("a", "b", "c")
        prefix = Path.of("a", "b")
        self.assertTrue(p.hasPrefix(prefix))


    def test_removingPrefix_withPrefix(self):
        p = Path.of("a", "b")

        self.assertEqual(p.removingPrefix(Path.of("a")), Path.of("b"))

    def test_removingPrefix_noPrefix(self):
        p = Path.of("a", "b")

        self.assertEqual(p.removingPrefix(Path.of("x")), Path.of("a", "b"))


    def test_commonPrefix_noCommon(self):
        a = Path.of("x")
        b = Path.of("y")
        self.assertEqual(list(a.commonPrefix(b)), [])

    def test_commonPrefix_withCommon(self):
        a = Path.of("a", "b", "c")
        b = Path.of("a", "b")
        self.assertEqual(list(a.commonPrefix(b)), ["a", "b"])


    def test_extractCommonPrefix(self):
        a = Path.of("a", "b", "c")
        b = Path.of("a", "b")
        prefix, rem_a, rem_b = a.extractCommonPrefix(b)

        self.assertEqual(prefix, ["a", "b"])
        self.assertEqual(rem_a, ["c"])
        self.assertEqual(rem_b, [])

    
    def test_lt(self):
        a = Path.of("a", "b", "c")
        b = Path.of("a", "b")
        c = Path.of()
        d = Path.of("a", "d")

        self.assertTrue(a > b)
        self.assertTrue(c < a)
        self.assertTrue(b < d)
        self.assertFalse(b > d)
        self.assertFalse(d < b)


    def test_str(self):
        ab  = Path.of("a", "b")
        a = Path.of("a")

        self.assertEqual(str(ab), "a > b")
        self.assertEqual(str(a), "a")


    def test_add(self):
        p = Path.of("a")
        result = p + ["b", "c"]

        self.assertEqual(result, ["a", "b", "c"])
        self.assertIsInstance(result, Path)

        with self.assertRaises(TypeError):
            _ = p + "b"


    def test_radd(self):
        p = Path.of("a")
        result = ["b", "c"] + p

        self.assertEqual(result, ["b", "c", "a"])
        self.assertIsInstance(result, Path)

        with self.assertRaises(TypeError):
            _ = "b" + p     


    def test_iadd(self):
        p = Path.of("a")
        ref = p
        p += ["b", "c"]
        self.assertIs(p, ref)
        self.assertEqual(list(p), ["a", "b", "c"])
        self.assertIsInstance(p, Path)

