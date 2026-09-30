from unittest import TestCase

from soil.data import Path, Value
from soil.data.type import ValueType
from soil.data.value import formatFloat

# Helper


value_int = Value(1)
value_float = Value(1.0)
value_str = Value("1")
value_path = Value(Path(("a", "b", "c")))
value_none = Value(None)
value_bytes = Value(b"\x00\xff")


class testValue(TestCase):

    def test_value_types(self):

        self.assertIs(value_int.type, ValueType.INTEGER)
        self.assertIs(value_float.type, ValueType.DOUBLE)
        self.assertIs(value_str.type, ValueType.STRING)
        self.assertIs(value_path.type, ValueType.PATH)
        self.assertIs(value_none.type, ValueType.NONE)
        self.assertIs(value_bytes.type, ValueType.DATA)


    def test_return_values(self):

        self.assertEqual(value_int.value, 1)
        self.assertEqual(value_float.value, 1.0)
        self.assertEqual(value_str.value, "1")
        self.assertEqual(value_path.value, ['a', 'b', 'c'])
        self.assertEqual(value_none.value, None)
        self.assertEqual(value_bytes.value, b'\x00\xff')


    def test_isNull(self):
        value_null = Value(None)
        value_not_null = Value(1)

        self.assertTrue(value_null.isNull)
        self.assertFalse(value_not_null.isNull)


    def test_str(self):

        self.assertEqual(str(value_int), "1")
        self.assertEqual(str(value_float), "1.0")
        self.assertEqual(str(value_str), "'1'")
        self.assertEqual(str(value_path), "a > b > c")
        self.assertEqual(str(value_none), "null")
        self.assertEqual(str(value_bytes), "00ff (DATA)")


    def test_eq(self):
        value_float_comp = Value(1.0)
        value_int_comp = Value(3)

        self.assertTrue(value_float == value_float_comp)
        self.assertFalse(value_int_comp == value_int)


    def test_formatFloat(self):
        x = 2.12345678
        x_formatted = formatFloat(x)

        self.assertEqual('2.1234567800000002', x_formatted)




