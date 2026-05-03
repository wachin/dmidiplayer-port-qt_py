"""Realtime sequence player for the first Python port."""

from __future__ import annotations

from bisect import bisect_left

from PyQt6.QtCore import QElapsedTimer, QObject, Qt, QTimer, pyqtSignal

from drumstick_py import MidiEvent, MidiOutputError
from .sequence import Sequence


class SequencePlayer(QObject):
    started = pyqtSignal()
    stopped = pyqtSignal()
    finished = pyqtSignal()
    positionChanged = pyqtSignal(int, int)
    eventPlayed = pyqtSignal(object)
    outputError = pyqtSignal(str)

    def __init__(self, output: object, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.sequence = Sequence(self)
        self.output = output
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._tick)
        self._events: list[MidiEvent] = []
        self._event_times_us: list[int] = []
        self._index = 0
        self._position = 0
        self._position_us = 0
        self._base_position_us = 0
        self._playing = False
        self._tempo_percent = 100
        self._pitch_shift = 0
        self._percussion_channel = 9
        self._clock = QElapsedTimer()

    def load_file(self, file_name: str) -> None:
        self.stop()
        self.sequence.load_file(file_name)
        self._events = self.sequence.events
        midi = self.sequence.midi
        self._event_times_us = [] if midi is None else [midi.event_microseconds(event) for event in self._events]
        self._index = 0
        self._position = 0
        self._position_us = 0
        self._base_position_us = 0
        self.positionChanged.emit(self._position, self.sequence.length_ticks)

    def play(self) -> None:
        if not self._events:
            return
        if self._index >= len(self._events):
            self._index = 0
            self._position = 0
            self._position_us = 0
        self._base_position_us = self._position_us
        self._clock.start()
        self._timer.start(2)
        self._playing = True
        self.started.emit()
        self._tick()

    def pause(self) -> None:
        self._position_us = self._elapsed_microseconds()
        self._timer.stop()
        self._playing = False
        self.stopped.emit()

    def stop(self) -> None:
        self._timer.stop()
        self.output.all_notes_off()
        self._playing = False
        self._index = 0
        self._position = 0
        self._position_us = 0
        self._base_position_us = 0
        self.positionChanged.emit(self._position, self.sequence.length_ticks)
        self.stopped.emit()

    def seek(self, tick: int) -> None:
        if not self._events:
            return
        was_playing = self._playing
        self._timer.stop()
        self.output.all_notes_off()

        self._position = max(0, min(tick, self.sequence.length_ticks))
        self._position_us = self.sequence.tick_to_microseconds(self._position)
        self._base_position_us = self._position_us
        self._index = bisect_left(self._event_times_us, self._position_us)
        self.positionChanged.emit(self._position, self.sequence.length_ticks)

        if was_playing and self._index < len(self._events):
            self._clock.start()
            self._timer.start(2)
            self._playing = True
        else:
            self._playing = False

    @property
    def tempo_percent(self) -> int:
        return self._tempo_percent

    def set_tempo_percent(self, value: int) -> None:
        value = max(50, min(200, value))
        if value == self._tempo_percent:
            return
        if self._playing:
            self._position_us = self._elapsed_microseconds()
            self._base_position_us = self._position_us
            self._clock.start()
        self._tempo_percent = value

    @property
    def pitch_shift(self) -> int:
        return self._pitch_shift

    def set_pitch_shift(self, semitones: int) -> None:
        self._pitch_shift = max(-12, min(12, semitones))

    def _tick(self) -> None:
        self._position_us = self._elapsed_microseconds()
        while self._index < len(self._events) and self._event_times_us[self._index] <= self._position_us:
            event = self._events[self._index]
            output_event = self._playable_event(event)
            try:
                if output_event is not None:
                    self.output.send_event(output_event)
            except MidiOutputError as exc:
                self._timer.stop()
                self.output.all_notes_off()
                self._playing = False
                self.outputError.emit(str(exc))
                self.stopped.emit()
                return
            self.eventPlayed.emit(output_event or event)
            self._position = event.tick
            self._index += 1
        self._position = min(
            self.sequence.microseconds_to_tick(self._position_us),
            self.sequence.length_ticks,
        )
        self.positionChanged.emit(self._position, self.sequence.length_ticks)
        if self._index >= len(self._events):
            self._timer.stop()
            self._playing = False
            self._position = self.sequence.length_ticks
            self._position_us = self.sequence.length_microseconds
            self._base_position_us = self._position_us
            self.positionChanged.emit(self._position, self.sequence.length_ticks)
            self.finished.emit()

    def _elapsed_microseconds(self) -> int:
        if not self._clock.isValid():
            return self._position_us
        elapsed = (self._clock.nsecsElapsed() // 1000) * self._tempo_percent // 100
        return self._base_position_us + elapsed

    def _playable_event(self, event: MidiEvent) -> MidiEvent | None:
        if self._pitch_shift == 0:
            return event
        if event.channel is None or event.channel == self._percussion_channel:
            return event
        if event.kind not in ("note_on", "note_off", "key_pressure") or not event.data:
            return event
        note = event.data[0] + self._pitch_shift
        if note < 0 or note > 127:
            return None
        return MidiEvent(
            tick=event.tick,
            kind=event.kind,
            channel=event.channel,
            data=bytes([note]) + event.data[1:],
            meta_type=event.meta_type,
        )
