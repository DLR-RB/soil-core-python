from __future__ import annotations

import json
import unittest
from collections.abc import Callable
from pathlib import Path as FsPath
from typing import Any

from soil.data.path import Path
from soil.data.sample import Sample
from soil.data.sampletree import SampleTree
from soil.data.timestamp import Timestamp
from soil.data.value import Value
from soil.encoding.binary import BinaryEncoding
from soil.encoding.json.json import JsonEncoding
from soil.encoding.json.min import CompactJsonEncoding
from soil.messaging.encoding import MessageEncoding
from soil.messaging.message import Message
from soil.messaging.message_type import MessageType

FIXTURE_PATH = FsPath(__file__).parent / "fixture.json"
ENCODINGS: dict[str, MessageEncoding] = {
    "json": JsonEncoding(),
    "compact": CompactJsonEncoding(),
}
BINARY_ENCODING: MessageEncoding = BinaryEncoding()


def _ts(seconds: float) -> Timestamp:
    return Timestamp.fromTimeIntervalSince1970(seconds)


def _msg(
    *,
    type: MessageType = MessageType.DATA,
    path: list[str] | None = None,
    samples: list[Sample] | None = None,
    children: dict[str, SampleTree] | None = None,
    count: int | None = None,
    depth: int | None = None,
    time: float | None = None,
    end: float | None = None,
    id: int | None = None,
) -> Message:
    """Build a Message exactly the way the decoders in json.py do."""
    tree = SampleTree(list(samples or []), dict(children or {}))
    return Message(
        type,
        Path(list(path or [])),
        tree,
        count,
        depth,
        None if time is None else _ts(time),
        None if end is None else _ts(end),
        id,
    )


CASES: dict[str, Callable[[], Message]] = {
    "none_value": lambda: _msg(samples=[Sample(Value(None), None)]),
    "integer_value": lambda: _msg(samples=[Sample(Value(42), None)]),
    "double_value": lambda: _msg(samples=[Sample(Value(2.5), None)]),
    "string_value_unicode": lambda: _msg(samples=[Sample(Value("héllo ✓"), None)]),
    "data_value": lambda: _msg(samples=[Sample(Value(bytes([0x00, 0x01, 0x02, 0xFE])), None)]),
    "path_value": lambda: _msg(samples=[Sample(Value(Path(["uplink", "bitrate"])), None)]),
    "list_value": lambda: _msg(
        samples=[Sample(Value([Value(1), Value("two"), Value(bytes([0x00]))]), None)]
    ),
    "map_value": lambda: _msg(
        samples=[Sample(Value({"alpha": Value(7), "beta": Value(2.5)}), None)]
    ),
    "nested_map_of_list": lambda: _msg(
        samples=[Sample(Value({"outer": Value([Value(1)])}), None)]
    ),
    "empty_list": lambda: _msg(samples=[Sample(Value([]), None)]),
    "empty_map": lambda: _msg(samples=[Sample(Value({}), None)]),
    "single_sample_with_timestamp": lambda: _msg(
        samples=[Sample(Value(1), _ts(123.5))]
    ),
    "multiple_samples": lambda: _msg(
        samples=[Sample(Value(1), _ts(10.0)), Sample(Value(2), _ts(20.0))]
    ),
    "tree_with_children": lambda: _msg(
        samples=[Sample(Value(1), None)],
        children={"child": SampleTree([Sample(Value("x"), None)])},
    ),
    "message_with_path": lambda: _msg(
        path=["telemetry", "temp"], samples=[Sample(Value(21.5), None)]
    ),
    "root_sample_with_message_time": lambda: _msg(
        samples=[Sample(Value(3), _ts(9.0))], time=50.0
    ),
    "message_time_end_id": lambda: _msg(time=1000.5, end=2000.25, id=7),
    "request_with_depth_zero": lambda: _msg(
        type=MessageType.REQUEST, path=["model"], depth=0
    ),
    "deletion": lambda: _msg(type=MessageType.DELETION, path=["old"]),
    "subscription_inclusion": lambda: _msg(
        type=MessageType.SUBSCRIPTION_INCLUSION, path=["tm"]
    ),
    "subscription_exclusion": lambda: _msg(
        type=MessageType.SUBSCRIPTION_EXCLUSION, path=["tm", "demo"]
    ),
    "subscription_deletion": lambda: _msg(
        type=MessageType.SUBSCRIPTION_DELETION, path=["tm"]
    ),
    "count_only": lambda: _msg(count=5),
}


def _load_vectors() -> dict[str, dict[str, Any]]:
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        document = json.load(f)
    return {case["name"]: case for case in document["cases"]}


class EncodingVectorTest(unittest.TestCase):
    """Compares our encoders/decoders against the shared known-good vectors."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.vectors = _load_vectors()

    def test_fixture_and_builders_are_in_sync(self) -> None:
        missing_builders = set(self.vectors) - set(CASES)
        missing_cases = set(CASES) - set(self.vectors)
        self.assertFalse(
            missing_builders or missing_cases,
            f"missing builders: {missing_builders}, "
            f"missing fixture cases: {missing_cases}",
        )

    def test_encode_matches_known_good(self) -> None:
        for name in sorted(CASES):
            message = CASES[name]()
            for wire_key, encoding in ENCODINGS.items():
                with self.subTest(case=name, encoding=wire_key):
                    actual = json.loads(encoding.encode(message))
                    expected = self.vectors[name][wire_key]
                    self.assertEqual(
                        actual,
                        expected,
                        f"{type(encoding).__name__} drift for case '{name}'",
                    )

    def test_decode_known_good_is_stable(self) -> None:
        for name in sorted(CASES):
            for wire_key, encoding in ENCODINGS.items():
                with self.subTest(case=name, encoding=wire_key):
                    expected = self.vectors[name][wire_key]
                    payload = json.dumps(expected).encode("utf-8")
                    decoded = encoding.decode(payload)
                    reencoded = json.loads(encoding.encode(decoded))
                    self.assertEqual(
                        reencoded,
                        expected,
                        f"{type(encoding).__name__} failed to decode known-good "
                        f"payload for case '{name}' without loss",
                    )

    def test_binary_matches_known_good(self) -> None:
        if not any(case.get("binary") for case in self.vectors.values()):
            self.skipTest("no binary vectors pinned yet")
        for name in sorted(CASES):
            expected_hex = self.vectors[name].get("binary")
            if not expected_hex:
                continue
            with self.subTest(case=name):
                actual = BINARY_ENCODING.encode(CASES[name]())
                self.assertEqual(
                    actual.hex(), expected_hex, f"binary drift for case '{name}'"
                )
                decoded = BINARY_ENCODING.decode(bytes.fromhex(expected_hex))
                self.assertEqual(
                    BINARY_ENCODING.encode(decoded).hex(),
                    expected_hex,
                    f"binary decode is lossy for case '{name}'",
                )


if __name__ == "__main__":
    unittest.main()