from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from drumstick_py import read_smf


def varlen(value: int) -> bytes:
    buffer = value & 0x7F
    value >>= 7
    while value:
        buffer <<= 8
        buffer |= (value & 0x7F) | 0x80
        value >>= 7
    out = bytearray()
    while True:
        out.append(buffer & 0xFF)
        if buffer & 0x80:
            buffer >>= 8
        else:
            return bytes(out)


def chunk(name: bytes, payload: bytes) -> bytes:
    return name + struct.pack(">I", len(payload)) + payload


class SmfParserTest(unittest.TestCase):
    def test_reads_tempo_metadata_and_note_events(self) -> None:
        header = chunk(b"MThd", struct.pack(">HHH", 0, 1, 480))
        track = b"".join(
            [
                varlen(0),
                b"\xff\x03",
                varlen(4),
                b"Test",
                varlen(0),
                b"\xff\x51",
                varlen(3),
                bytes([0x07, 0xA1, 0x20]),
                varlen(0),
                bytes([0x90, 60, 100]),
                varlen(480),
                bytes([0x80, 60, 0]),
                varlen(0),
                b"\xff\x2f\x00",
            ]
        )
        data = header + chunk(b"MTrk", track)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir, "simple.mid")
            path.write_bytes(data)
            midi = read_smf(path)

        note_events = [event for event in midi.events if event.kind in ("note_on", "note_off")]
        self.assertEqual(midi.title, "Test")
        self.assertEqual(midi.tempo_changes[0].microseconds_per_quarter, 500_000)
        self.assertEqual(midi.length_ticks, 480)
        self.assertEqual(midi.length_microseconds, 500_000)
        self.assertEqual([event.kind for event in note_events], ["note_on", "note_off"])
        self.assertEqual(midi.microseconds_to_tick(250_000), 240)
        self.assertTrue(any(event.kind == "meta" and event.meta_type == 0x2F for event in midi.events))


if __name__ == "__main__":
    unittest.main()
