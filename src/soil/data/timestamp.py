from datetime import datetime, timezone
from .convertible import ValueConvertible
from .value import Value

class Timestamp(datetime, ValueConvertible):
    """
    A SOIL timestamp.

    All timestamps are in UTC.
    """

    @classmethod
    def current(cls) -> 'Timestamp':
        """ The current time in UTC """
        return cls.now(tz=timezone.utc)

    def adding(self, interval: float) -> 'Timestamp':
        """ Create a new timestamp by adding the given interval to this timestamp """
        seconds = self.timeIntervalSince1970 + interval
        return Timestamp.fromTimeIntervalSince1970(seconds)

    @property
    def timeIntervalSince1970(self) -> float:
        """ The seconds since 1.1.1970 """
        return self.timestamp()

    @classmethod
    def fromTimeIntervalSince1970(cls, seconds: float) -> 'Timestamp':
        """ Create a timestamp from the seconds since 1.1.1970 """
        return cls.fromtimestamp(seconds, timezone.utc)

    @classmethod
    def fromDatetime(cls, dt: datetime) -> 'Timestamp':
        """ Create a timestamp from a datetime object """
        return cls(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second,
            dt.microsecond,
            tzinfo = dt.tzinfo,
            fold = dt.fold,
        )

    def format(self) -> str:
        """ Convert the timestamp to a string with the date and time """
        return self.strftime("%d.%m.%Y %H:%M:%S")

    def isVeryCloseTo(self, other: 'Timestamp', maxDifference: float = 0.001) -> bool:
        return abs(self.timestamp() - other.timestamp()) < maxDifference


    @classmethod
    def fromValue(cls, value: Value) -> Timestamp:
        """
        Create a timestamp from a DOUBLE value (seconds since 1970).

        Raises
        ------
        TypeError
            If ``value`` is not a ``Value``.
        ValueError
            If ``value`` is not a DOUBLE.
        """
        if not isinstance(value, Value):
            raise TypeError(f"expected a Value, got {type(value).__name__}")
        seconds = value.doubleValue
        if seconds is None:
            raise ValueError(f"expected a DOUBLE value, got {value.type}")
        return cls.fromTimeIntervalSince1970(seconds)

    def toValue(self) -> Value:
        """ Convert timestamp into value type"""
        return Value(self.timeIntervalSince1970)