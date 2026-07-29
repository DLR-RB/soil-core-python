from typing import override

from ..components import Receiver
from ..data import Path, SampleTree, Timestamp
from ..requests import Request, CompletedRequest


class PrintReceiver(Receiver):
    """
    A simple receiver that prints all received data to stdout.
    """

    def __init__(self, dateFormat: str = "%H:%M:%S %d.%m.%Y") -> None:
        """
        Create a receiver that prints to stdout using a European date format.

        :param dateFormat: The date format string to use for timestamps.
        """
        self._dateFormat = dateFormat

    @override
    def accept(
        self,
        tree: SampleTree,
        path: Path,
    ) -> Request:
        self._print(tree, path)
        return CompletedRequest()

    def convertPath(self, path: Path) -> str:
        return ">".join(path)

    def convertTime(self, time: Timestamp | None) -> str:
        if time is None:
            return "Now"

        return time.astimezone().strftime(
            self._dateFormat
        )

    def _print(
        self,
        tree: SampleTree,
        path: Path,
    ) -> None:
        pathString = self.convertPath(path)

        for sample in tree.samples:
            timeString = self.convertTime(sample.timestamp)

            print(f"{pathString}: {sample.value} ({timeString})")

        for name, child in tree.children.items():
            self._print(child, path.appending(name))
