from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from drumstick_py import BackendManager, MidiFileError, MidiOutputError, PianoKeyboard
from .player import SequencePlayer


class MainWindow(QMainWindow):
    def __init__(self, start_files: list[str]) -> None:
        super().__init__()
        self.setWindowTitle("dmidiplayer PyQt6")
        self.resize(900, 520)
        self.manager = BackendManager(self)
        self.output = self._create_midi_output()
        self.player = SequencePlayer(self.output, self)
        self.player.positionChanged.connect(self._update_position)
        self.player.eventPlayed.connect(self._event_played)
        self.player.outputError.connect(self._output_error)
        self.player.finished.connect(self._finished)

        self.playlist = QListWidget()
        self.playlist.itemDoubleClicked.connect(lambda item: self.load_file(item.text()))
        self.title_label = QLabel("No hay archivo cargado")
        self.title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.position = QSlider(Qt.Orientation.Horizontal)
        self.position.setTracking(False)
        self.position.setEnabled(False)
        self.position.sliderReleased.connect(self._seek_to_slider)
        self.keyboard = PianoKeyboard()
        self.event_label = QLabel(f"Salida MIDI: {self.output.name}")
        self.connection_combo = QComboBox()
        self.connection_combo.setMinimumWidth(260)
        self._updating_position = False

        self._build_toolbar()
        self._build_layout()
        self._refresh_midi_connections(autoconnect=True)
        for file_name in start_files:
            self.add_file(file_name)
        if start_files:
            self.load_file(start_files[0])

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Reproduccion", self)
        self.addToolBar(toolbar)
        open_action = QAction(QIcon.fromTheme("document-open"), "Abrir", self)
        open_action.triggered.connect(self.open_files)
        toolbar.addAction(open_action)
        toolbar.addSeparator()
        for text, slot in (("Reproducir", self.player.play), ("Pausa", self.player.pause), ("Detener", self.player.stop)):
            button = QPushButton(text)
            button.clicked.connect(slot)
            toolbar.addWidget(button)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Tono:"))
        pitch = QSpinBox()
        pitch.setRange(-12, 12)
        pitch.setValue(0)
        pitch.valueChanged.connect(self.player.set_pitch_shift)
        toolbar.addWidget(pitch)
        reset_pitch = QPushButton("0")
        reset_pitch.clicked.connect(lambda: pitch.setValue(0))
        toolbar.addWidget(reset_pitch)
        toolbar.addWidget(QLabel("Tempo:"))
        tempo = QSpinBox()
        tempo.setRange(50, 200)
        tempo.setValue(100)
        tempo.setSuffix("%")
        tempo.valueChanged.connect(self.player.set_tempo_percent)
        toolbar.addWidget(tempo)
        reset_tempo = QPushButton("100%")
        reset_tempo.clicked.connect(lambda: tempo.setValue(100))
        toolbar.addWidget(reset_tempo)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Destino MIDI:"))
        toolbar.addWidget(self.connection_combo)
        refresh_button = QPushButton("Refrescar")
        refresh_button.clicked.connect(self._refresh_midi_connections)
        toolbar.addWidget(refresh_button)
        connect_button = QPushButton("Conectar")
        connect_button.clicked.connect(self._connect_selected_midi_output)
        toolbar.addWidget(connect_button)

    def _build_layout(self) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        left = QVBoxLayout()
        left.addWidget(QLabel("Lista"))
        left.addWidget(self.playlist)
        right = QVBoxLayout()
        right.addWidget(self.title_label)
        right.addWidget(self.position)
        right.addWidget(self.keyboard)
        right.addWidget(self.event_label)
        root.addLayout(left, 1)
        root.addLayout(right, 3)
        self.setCentralWidget(central)

    def _create_midi_output(self) -> object:
        try:
            return self.manager.create_output("alsa")
        except MidiOutputError as exc:
            info = self.manager.alsa_audio_info()
            suffix = f" Tarjetas detectadas por python3-alsaaudio: {len(info.cards)}." if info.available else ""
            self.statusBar().showMessage(f"ALSA no disponible, usando dummy: {exc}.{suffix}", 10000)
            return self.manager.create_output("dummy")

    def _refresh_midi_connections(self, autoconnect: bool = False) -> None:
        self.connection_combo.clear()
        if not hasattr(self.output, "connections"):
            self.connection_combo.addItem("Dummy output")
            self.connection_combo.setEnabled(False)
            return
        try:
            connections = self.output.connections()
        except MidiOutputError as exc:
            self.connection_combo.addItem("Sin destinos ALSA")
            self.connection_combo.setEnabled(False)
            self.statusBar().showMessage(str(exc), 10000)
            return
        self.connection_combo.setEnabled(bool(connections))
        if not connections:
            self.connection_combo.addItem("Sin destinos ALSA")
            self.statusBar().showMessage("No se encontraron destinos MIDI ALSA. Abre QSynth y pulsa Refrescar.", 10000)
            return
        for connection in connections:
            self.connection_combo.addItem(connection.name, connection)
        if autoconnect:
            self._autoconnect_preferred_midi_output(connections)

    def _autoconnect_preferred_midi_output(self, connections: list[object]) -> None:
        preferred = next(
            (
                connection
                for connection in connections
                if any(token in connection.name.casefold() for token in ("qsynth", "fluidsynth", "fluid"))
            ),
            None,
        )
        if preferred is None:
            return
        index = connections.index(preferred)
        self.connection_combo.setCurrentIndex(index)
        self._connect_midi_output(preferred)

    def _connect_selected_midi_output(self) -> None:
        connection = self.connection_combo.currentData()
        if connection is None:
            self.statusBar().showMessage("No hay destino MIDI ALSA seleccionado", 5000)
            return
        self._connect_midi_output(connection)

    def _connect_midi_output(self, connection: object) -> None:
        if not hasattr(self.output, "connect_to"):
            self.statusBar().showMessage("La salida dummy no permite conexiones ALSA", 5000)
            return
        try:
            self.output.connect_to(connection)
        except MidiOutputError as exc:
            QMessageBox.warning(self, "Conexion MIDI", str(exc))
            return
        self.statusBar().showMessage(f"Conectado a {connection.name}", 10000)
        self.event_label.setText(f"Salida MIDI: {self.output.name} -> {connection.name}")

    def open_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Abrir MIDI",
            str(Path.home()),
            "MIDI (*.mid *.midi *.kar);;Todos los archivos (*)",
        )
        for file_name in files:
            self.add_file(file_name)
        if files:
            self.load_file(files[0])

    def add_file(self, file_name: str) -> None:
        path = Path(file_name)
        if path.exists():
            self.playlist.addItem(str(path))

    def load_file(self, file_name: str) -> None:
        try:
            self.player.load_file(file_name)
        except (OSError, MidiFileError) as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return
        midi = self.player.sequence.midi
        if midi is None:
            return
        duration = midi.length_microseconds / 1_000_000
        self.title_label.setText(
            f"{midi.title} - formato {midi.format}, {len(midi.tracks)} pista(s), "
            f"{midi.length_ticks} ticks, {duration:.1f} s"
        )
        self.event_label.setText("Archivo cargado")
        self.position.setEnabled(midi.length_ticks > 0)
        self.keyboard.clear()

    def _update_position(self, tick: int, maximum: int) -> None:
        self._updating_position = True
        self.position.setMaximum(maximum)
        self.position.setValue(min(tick, maximum))
        self._updating_position = False

    def _seek_to_slider(self) -> None:
        if self._updating_position:
            return
        self.player.seek(self.position.value())
        self.keyboard.clear()

    def _event_played(self, event: object) -> None:
        kind = getattr(event, "kind", "event")
        channel = getattr(event, "channel", None)
        data = getattr(event, "data", b"")
        self.event_label.setText(f"{kind} canal={channel if channel is not None else '-'} datos={data.hex(' ')}")
        if kind == "note_on" and len(data) >= 2 and data[1] > 0:
            self.keyboard.note_on(data[0])
        elif kind in ("note_off", "note_on") and data:
            self.keyboard.note_off(data[0])

    def _finished(self) -> None:
        self.event_label.setText("Fin de la secuencia")
        self.keyboard.clear()

    def _output_error(self, message: str) -> None:
        self.event_label.setText(f"Error de salida MIDI: {message}")
        self.statusBar().showMessage(message, 10000)
        QMessageBox.warning(self, "Salida MIDI", message)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="dmidiplayer PyQt6 port")
    parser.add_argument("files", nargs="*", help="Archivos SMF/KAR")
    args = parser.parse_args(argv)
    app = QApplication(sys.argv[:1] + args.files)
    app.setApplicationName("dmidiplayer-py")
    window = MainWindow(args.files)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
