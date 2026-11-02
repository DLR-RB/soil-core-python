from unittest import TestCase

from soil.data import Path, Value
from soil.data.type import ValueType
from soil.data.value import formatFloat

# Helper

class _Dummy:
    def __str__(self): return "false type"

value_int = Value(1)
value_float = Value(1.0)
value_str = Value("1")
value_path = Value(Path(("a", "b", "c")))
value_none = Value(None)
value_bytes = Value(b"\x00\xff")
value_list = Value([Value(1), Value(2)])
value_dict = Value({"value": Value(1)})
value_no = Value(_Dummy())


class testValue(TestCase):

    def test_value_types(self):

        self.assertIs(value_int.type, ValueType.INTEGER)
        self.assertIs(value_float.type, ValueType.DOUBLE)
        self.assertIs(value_str.type, ValueType.STRING)
        self.assertIs(value_path.type, ValueType.PATH)
        self.assertIs(value_none.type, ValueType.NONE)
        self.assertIs(value_bytes.type, ValueType.DATA)
        self.assertIs(value_list.type, ValueType.LIST)
        self.assertIs(value_dict.type, ValueType.MAP)

    def test_return_values(self):

        self.assertEqual(value_int.value, 1)
        self.assertEqual(value_float.value, 1.0)
        self.assertEqual(value_str.value, "1")
        self.assertEqual(value_path.value, ['a', 'b', 'c'])
        self.assertEqual(value_none.value, None)
        self.assertEqual(value_bytes.value, b'\x00\xff')
        self.assertEqual(value_list.value, [Value(1), Value(2)])
        self.assertEqual(value_dict.value, {"value": Value(1)})


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
        self.assertEqual(str(value_list), "1, 2")
        self.assertEqual(str(value_dict), "value = 1")
        self.assertEqual(str(value_no), "false type (Unknown)")


    def test_eq(self):
        value_float_comp = Value(1.0)
        value_int_comp = Value(3)

        self.assertTrue(value_float == value_float_comp)
        self.assertFalse(value_int_comp == value_int)
        self.assertFalse(value_no == value_int)
        self.assertFalse(1 == value_int)


    def test_formatFloat(self):
        x = 2.12345678
        x_formatted = formatFloat(x)

        self.assertEqual('2.1234567800000002', x_formatted)


    def test_fromValue(self):
        value = Value(1)
        not_value = 1

        self.assertEqual(value, Value.fromValue(value))
        with self.assertRaises(TypeError):
            _ = Value.fromValue(not_value)


    
    def test_IntValue(self):
        num = Value(1)
        no_num = Value("a")

        self.assertEqual(num.intValue, 1)
        self.assertEqual(no_num.intValue, None)


    def test_StrValue(self):
        text = Value("a")
        no_text = Value(1)

        self.assertEqual(text.stringValue, "a")
        self.assertEqual(no_text.stringValue, None)


    def test_DoubleValue(self):
        num = Value(1.0)
        no_num = Value("a")

        self.assertEqual(num.doubleValue, 1.0)
        self.assertEqual(no_num.doubleValue, None)


    def test_DataValue(self):
        data = Value(b"\x00\xff")
        no_data = Value(1)

        self.assertEqual(data.dataValue, b"\x00\xff")
        self.assertEqual(no_data.dataValue, None)

    def test_PathValue(self):
        p = Value(Path.of("a"))
        no_p = Value(1)

        self.assertEqual(p.pathValue, ["a"])
        self.assertEqual(no_p.pathValue, None)

    def test_IsNull(self):
        value = Value(None)
        value_value = Value(1)

        self.assertTrue(value.isNull)
        self.assertFalse(value_value.isNull)

    def test_ListValue(self):
        values = Value([Value(1), Value(2)])
        p = Value(Path.of("a", "b"))

        self.assertEqual(values.listValue, [Value(1), Value(2)])
        self.assertEqual(p.listValue, None)

    def test_MapValue(self):
        values = Value({"value": Value(1)})
        p = Value(Path.of("a", "b"))

        self.assertEqual(values.mapValue, {"value": Value(1)})
        self.assertEqual(p.mapValue, None)       


    def test_Getitem(self):
        v = Value({"name": Value("value"), "n": Value(1)})
        v_list = Value([Value(1)])
        value_noMap = Value(1)

        self.assertEqual(v["name"], Value("value"))
        self.assertEqual(v["n"], Value(1))

        with self.assertRaises(KeyError):
            _ = v["a"]

        with self.assertRaises(TypeError):
            _ = value_noMap["a"]        

        self.assertEqual(v_list[0], Value(1))

        with self.assertRaises(IndexError):
            _ = v_list[1]  

        with self.assertRaises(TypeError):
            _ = value_noMap[0]

        with self.assertRaises(TypeError):
            _ = v[3.14]


    def test_Contains(self):
        v = Value({"a": Value(1), "b": Value(2)})

        self.assertIn("a", v)
        self.assertNotIn("c", v)

        v = Value([Value(1), Value(2), Value(3)])

        self.assertIn(Value(2), v)
        self.assertNotIn(Value(4), v)

        v = Value(1)
        with self.assertRaises(TypeError):
            _ = "x" in v

    def test_Iter(self):
        v = Value([Value(1), Value(2), Value(3)])
        result = list(v)

        self.assertEqual(result, [Value(1), Value(2), Value(3)])       

        v = Value({"x": Value(1), "y": Value(2)})
        keys = list(v)

        self.assertEqual(keys, ["x", "y"])

        v = Value(1)

        with self.assertRaises(TypeError):
            _ = list(v)

        v = Value(None)

        with self.assertRaises(TypeError):
            _ = list(v)

        