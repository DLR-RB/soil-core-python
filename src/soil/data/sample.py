from dataclasses import dataclass
from functools import total_ordering
from typing import Self

from .timestamp import Timestamp
from .value import Value

@total_ordering
@dataclass(frozen=True, slots=True)
class Sample:
    """
    A value with a timestamp.
    """

    #: The value associated with the timestamp.
    value: Value

    #: The timestamp of the value.
    timestamp: Timestamp | None = None

    @property
    def time(self) -> Timestamp:
        """
        The timestamp of the sample, or the current time.

        Returns
        -------
        Timestamp
            The sample timestamp if present, otherwise the current
            timestamp.
        """
        return self.timestamp if self.timestamp is not None else Timestamp.current()

    @classmethod
    def fromUnixTimestamp(
        cls,
        value: Value,
        time_interval_since_1970: float,
    ) -> Self:
        """
        Create a timestamped value from a Unix timestamp.

        Parameters
        ----------
        value:
            The contained value.
        timestamp:
            Seconds since the Unix epoch.

        Returns
        -------
        Self
            A timestamped sample.
        """
        return cls(
            value=value,
            timestamp=Timestamp.fromTimeIntervalSince1970(time_interval_since_1970),
        )

    def withTimeSet(self) -> Self:
        """
        Set the timestamp to the current time if it is not already set.

        Returns
        -------
        Self
            This sample if a timestamp is already present,
            otherwise a copy with the current timestamp.
        """
        if self.timestamp is not None:
            return self

        return type(self)(
            value=self.value,
            timestamp=Timestamp.current(),
        )

    def isVeryCloseTo(self, other: Timestamp, maxDifference: float = 0.001) -> bool:
        return self.time.isVeryCloseTo(other, maxDifference)

    def __lt__(self, other: object) -> bool:
        """
        Compare samples chronologically.

        Notes
        -----
        A timestamp of ``None`` represents the end of time.

        Therefore:

        - ``Sample(timestamp=None)`` is greater than every
          timestamped sample.
        - Two ``None`` timestamps compare as equal.
        """
        if not isinstance(other, Sample):
            return NotImplemented

        lhs_time = self.timestamp
        rhs_time = other.timestamp

        if lhs_time is None:
            # end of time
            return False

        if rhs_time is None:
            # finite < end of time
            return True

        return lhs_time < rhs_time

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Sample):
            return False
        return value.value == self.value and value.timestamp == self.timestamp

    def __str__(self) -> str:
        """
        Return a human-readable representation.

        Returns
        -------
        str
            A string in the form:
            '<value> (<timestamp>)'
        """
        if self.timestamp is None:
            time_string = "now"
        else:
            time_string = self.timestamp.format()

        return f"{self.value} ({time_string})"