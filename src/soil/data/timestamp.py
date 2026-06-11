from datetime import datetime, timezone


class Timestamp(datetime):
    """
    A SOIL timestamp.

    All timestamps are in UTC.
    """

    @classmethod
    def current(cls) -> 'Timestamp':
        """ The current time in UTC """
        return cls.now(tz=timezone.utc)

    def adding(self, interval: float) -> Timestamp:
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

    def format(self) -> str:
        """ Convert the timestamp to a string with the date and time """
        return self.strftime("%d.%m.%Y %H:%M:%S")
