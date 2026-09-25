from unittest import TestCase, main
from unittest.mock import patch, MagicMock

from soil.data import Sample, Path, Value, Timestamp

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
class testSampleTimeProperty(TestCase):

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


    def test_eq(self, mock_current):
        sample_with_timestamp = Sample(Value(1.0), mockTimestamp)
        sample_with_timestamp_2 = Sample(Value(1.0), mockTimestamp)
        sample_wrong_value = Sample(Value(1.5), mockTimestamp)
        sample_wrong_timestamp = Sample(Value(1.0), mockTimestamp_plus_1)


        self.assertTrue(sample_with_timestamp == sample_with_timestamp_2)
        self.assertFalse(sample_with_timestamp == sample_wrong_value)
        self.assertFalse(sample_with_timestamp == sample_wrong_timestamp)


    def test_str(self, mock_current):
        sample_with_timestamp = Sample(Value(1.0), mockTimestamp)
        sample_no_timestamp = Sample(Value(3.0))

        self.assertEqual(str(sample_with_timestamp), f"{1.0} ({mockTimestamp.format()})")
        self.assertEqual(str(sample_no_timestamp), f"{3.0} (now)")
