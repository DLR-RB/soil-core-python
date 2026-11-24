from unittest import TestCase
from unittest.mock import MagicMock, patch

from soil.data import Path, Sample, Timestamp, Value, ValueType

# Helper

mockTimestamp = Timestamp(1, 1, 1, 1, 1, 2)

mockTimestamp_plus_1 = Timestamp(1, 1, 1, 1, 1, 3)


MOCK_CURRENT_TIME = MagicMock(name="MOCK_CURRENT_TIME", spec=Timestamp)

MOCK_CURRENT_TIME_PLUS_1 = MagicMock(name="MOCK_CURRENT_TIME_PLUS_1", spec=Timestamp)

MOCK_CURRENT_TIME.adding.return_value = MOCK_CURRENT_TIME_PLUS_1

MOCK_CURRENT_TIME.format.return_value = "2026-09-09 09:09:09.009"

MOCK_CURRENT_TIME_PLUS_1.format.return_value = "2026-09-09 09:09:10.009"


# Tests
@patch('soil.data.sample.Timestamp.current', return_value=MOCK_CURRENT_TIME)
class testSample(TestCase):

    def test_time_returns_timestamp(self, mock_current):
        sample = Sample(value=Value(3.0), timestamp=mockTimestamp)

        self.assertEqual(sample.time, mockTimestamp)


    def test_time_returns_current(self, mock_current):
        sample = Sample(value=Value(3.0))

        self.assertEqual(sample.time, MOCK_CURRENT_TIME)


    def test_fromUnixTimestamp(self, mock_current):
        sample = Sample.fromUnixTimestamp(Value(3.0), 1)

        sample_control = Timestamp.fromTimeIntervalSince1970(1)

        self.assertEqual(sample.time, sample_control)


    def test_withTimeSet(self, mock_current):
        sample = Sample(Value(3.0))
        sample_with_timestamp = Sample(Value(1.0), Timestamp.current().adding(1.0))

        self.assertEqual(sample.withTimeSet().time, MOCK_CURRENT_TIME)
        self.assertEqual(sample_with_timestamp, Sample(Value(1.0), MOCK_CURRENT_TIME_PLUS_1))


    def test_isVeryCloseTo(self, mock_current):
        sample_with_timestamp = Sample(Value(1.0), Timestamp.current())

        self.assertTrue(sample_with_timestamp.isVeryCloseTo(MOCK_CURRENT_TIME_PLUS_1))


    def test_lt_samples(self, mock_current): #less then
        sample_with_timestamp = Sample(Value(1.0), mockTimestamp)
        sample_with_timestamp_bigger = Sample(Value(1.0), mockTimestamp_plus_1)

        self.assertFalse(sample_with_timestamp_bigger < sample_with_timestamp)
        self.assertTrue(sample_with_timestamp_bigger > sample_with_timestamp)

    def test_lt_none(self, mock_current): #less then
            sample_with_timestamp = Sample(Value(1.0), mockTimestamp)
            sample_no_timestamp = Sample(Value(1.0))
    
            self.assertTrue(sample_no_timestamp > sample_with_timestamp)
            self.assertFalse(sample_with_timestamp > sample_no_timestamp)

    def test_lt_no_Instance(self, _):
        no_sample = Value(1)
        sample = Sample(Value(2))
        
        with self.assertRaises(TypeError):
            _ = no_sample < sample


    def test_eq(self, mock_current):
        sample_with_timestamp = Sample(Value(1.0), mockTimestamp)
        sample_with_timestamp_2 = Sample(Value(1.0), mockTimestamp)
        sample_wrong_value = Sample(Value(1.5), mockTimestamp)
        sample_wrong_timestamp = Sample(Value(1.0), mockTimestamp_plus_1)
        sample_no_sample = (Value(1.0), mockTimestamp)


        self.assertTrue(sample_with_timestamp == sample_with_timestamp_2)
        self.assertFalse(sample_with_timestamp == sample_wrong_value)
        self.assertFalse(sample_with_timestamp == sample_wrong_timestamp)
        self.assertFalse(sample_no_sample == sample_with_timestamp)


    def test_str(self, mock_current):
        sample_with_timestamp = Sample(Value(1.0), mockTimestamp)
        sample_no_timestamp = Sample(Value(3.0))

        self.assertEqual(str(sample_with_timestamp), f"{1.0} ({mockTimestamp.format()})")
        self.assertEqual(str(sample_no_timestamp), f"{3.0} (now)")


    def test_repr(self, mock_current):
        ts = Timestamp(1, 1, 1)
        val = Value("test")
        sample = Sample(val, ts)
        sample_no_ts = Sample(val)

        expected = f"Sample(value={val!r}, timestamp={ts!r})"
        expected_no_ts = f"Sample(value={val!r}, timestamp=None)"

        self.assertEqual(repr(sample), expected)
        self.assertEqual(repr(sample_no_ts), expected_no_ts)


# Tests for Sample with AnyValue support (new convenience)
class testSampleWithAnyValue(TestCase):
    """Test Sample can be created with AnyValue (raw types)"""

    def test_sample_with_int(self):
        sample = Sample(42)
        self.assertEqual(sample.value, Value(42))
        self.assertIsNone(sample.timestamp)

    def test_sample_with_string(self):
        sample = Sample("hello")
        self.assertEqual(sample.value, Value("hello"))

    def test_sample_with_float(self):
        sample = Sample(3.14)
        self.assertEqual(sample.value, Value(3.14))

    def test_sample_with_bytes(self):
        sample = Sample(b"test")
        self.assertEqual(sample.value, Value(b"test"))

    def test_sample_with_path(self):
        path = Path.of("a", "b")
        sample = Sample(path)
        self.assertEqual(sample.value, Value(path))

    def test_sample_with_list(self):
        sample = Sample([1, 2, 3])
        self.assertEqual(sample.value, Value([1, 2, 3]))

    def test_sample_with_dict(self):
        sample = Sample({"key": "value"})
        # Check the type and that it's a Value containing a dict
        self.assertEqual(sample.value.type, ValueType.MAP)
        # The dict values are stored as-is (strings in this case)
        self.assertEqual(sample.value.mapValue["key"], "value")

    def test_sample_with_none(self):
        sample = Sample(None)
        self.assertEqual(sample.value, Value(None))

    def test_sample_with_timestamp(self):
        # Timestamp is a ValueConvertible, so it should be converted to Value
        ts = Timestamp(2026, 11, 24, 10, 30, 0)
        sample = Sample(ts)
        self.assertIsNotNone(sample.value)

    def test_sample_with_value_still_works(self):
        sample = Sample(Value(100))
        self.assertEqual(sample.value, Value(100))
