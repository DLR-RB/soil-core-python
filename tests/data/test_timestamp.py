from datetime import UTC, datetime
from unittest import TestCase, main

from soil.data import Timestamp


class TimestampTests(TestCase):

    def testCurrentTime(self):
        now = datetime.now(tz=UTC)
        current = Timestamp.current()

        self.assertAlmostEqual(now.timestamp(), current.timestamp(), 3)

    def testIsClose(self):
        current = Timestamp.current()
        later = current.adding(0.0005)

        self.assertTrue(current.isVeryCloseTo(later))
        self.assertTrue(later.isVeryCloseTo(current))

    def testIsNotClose(self):
        current = Timestamp.current()
        later = current.adding(0.002)

        self.assertFalse(current.isVeryCloseTo(later))
        self.assertFalse(later.isVeryCloseTo(current))

    def testIsCloseCustom(self):
        current = Timestamp.current()
        later = current.adding(0.02)

        self.assertTrue(current.isVeryCloseTo(later, 0.05))
        self.assertTrue(later.isVeryCloseTo(current, 0.05))
        self.assertFalse(current.isVeryCloseTo(later, 0.01))
        self.assertFalse(later.isVeryCloseTo(current, 0.01))


if __name__ == "__main__":
    main()
