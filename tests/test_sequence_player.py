from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from dmidiplayer_py.player import SequencePlayer


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


def write_simple_midi(path: Path) -> None:
    header = chunk(b"MThd", struct.pack(">HHH", 0, 1, 480))
    track = b"".join(
        [
            varlen(0),
            b"\xff\x51\x03\x07\xa1\x20",
            varlen(0),
            bytes([0x90, 60, 100]),
            varlen(480),
            bytes([0x80, 60, 0]),
            varlen(0),
            b"\xff\x2f\x00",
        ]
    )
    path.write_bytes(header + chunk(b"MTrk", track))


class OutputStub:
    def __init__(self) -> None:
        self.all_notes_off_count = 0

    def send_event(self, event: object) -> None:
        pass

    def all_notes_off(self) -> None:
        self.all_notes_off_count += 1


class SequencePlayerTest(unittest.TestCase):
    def test_seek_updates_position_and_next_event(self) -> None:
        output = OutputStub()
        player = SequencePlayer(output)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir, "simple.mid")
            write_simple_midi(path)
            player.load_file(str(path))

        player.seek(240)

        self.assertEqual(player._position, 240)
        self.assertEqual(player._position_us, 250_000)
        self.assertEqual(player._index, 2)
        self.assertGreaterEqual(output.all_notes_off_count, 1)


if __name__ == "__main__":
    unittest.main()
