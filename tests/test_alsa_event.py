from __future__ import annotations

import unittest

from drumstick_py.rt import (
    AlsaSequencerOutput,
    SND_SEQ_EVENT_LENGTH_MASK,
    SND_SEQ_EVENT_LENGTH_VARIABLE,
    SND_SEQ_EVENT_SYSEX,
)


class AlsaEventTest(unittest.TestCase):
    def test_sysex_event_is_marked_as_variable_length(self) -> None:
        class OutputStub:
            _port = 0

            def _base_event(self, event_type: int):
                return AlsaSequencerOutput._base_event(self, event_type)

        output = OutputStub()

        event = AlsaSequencerOutput._make_sysex_event(output, bytes.fromhex("41 10 42 12 40 00 7f 00 41 f7"))

        self.assertEqual(event.type, SND_SEQ_EVENT_SYSEX)
        self.assertEqual(event.flags & SND_SEQ_EVENT_LENGTH_MASK, SND_SEQ_EVENT_LENGTH_VARIABLE)
        self.assertEqual(event.data.ext.len, 11)
        self.assertTrue(event._payload.raw.startswith(b"\xf0\x41"))
        self.assertTrue(event._payload.raw.endswith(b"\xf7\x00"))


if __name__ == "__main__":
    unittest.main()
