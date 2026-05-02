"""Python/PyQt6 porting layer for Drumstick.

This package is intentionally small at the beginning of the port.  It exposes
the same broad areas as the C++ project: MIDI file handling, realtime outputs,
and reusable widgets.
"""

from .file import (
    KeySignature,
    MidiEvent,
    MidiFile,
    MidiFileError,
    MidiTrack,
    TempoChange,
    TextEvent,
    TimeSignature,
    read_smf,
)
from .rt import (
    AlsaAudioInfo,
    AlsaSequencerOutput,
    BackendManager,
    DummyMidiOutput,
    MIDI_STD_CHANNELS,
    MidiConnection,
    MidiOutputError,
    alsa_audio_info,
    list_alsa_output_ports,
)
from .widgets import PianoKeyboard

__all__ = [
    "AlsaAudioInfo",
    "AlsaSequencerOutput",
    "BackendManager",
    "DummyMidiOutput",
    "KeySignature",
    "MIDI_STD_CHANNELS",
    "MidiConnection",
    "MidiOutputError",
    "alsa_audio_info",
    "list_alsa_output_ports",
    "MidiEvent",
    "MidiFile",
    "MidiFileError",
    "MidiTrack",
    "PianoKeyboard",
    "TempoChange",
    "TextEvent",
    "TimeSignature",
    "read_smf",
]
