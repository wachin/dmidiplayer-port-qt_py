"""Translation helpers for the PyQt6 port."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QLocale, QTranslator
from PyQt6.QtWidgets import QApplication


TRANSLATIONS_DIR = Path(__file__).resolve().parent / "translations"


def install_translator(app: QApplication, language: str = "en") -> str:
    """Install an application translator and return the language actually used.

    English is the source language, so it does not need a translator file.
    Other languages are loaded from ``dmidiplayer_py/translations`` as compiled
    ``.qm`` files named like ``dmidiplayer_py_es.qm``.
    """

    requested = (language or "en").replace("-", "_")
    if requested == "system":
        requested = QLocale.system().name()
    if requested.casefold().startswith("en"):
        return "en"

    candidates = [requested]
    base = requested.split("_", 1)[0]
    if base != requested:
        candidates.append(base)

    for candidate in candidates:
        translator = QTranslator(app)
        path = TRANSLATIONS_DIR / f"dmidiplayer_py_{candidate}.qm"
        if translator.load(str(path)):
            app.installTranslator(translator)
            app._dmidiplayer_translator = translator
            return candidate
    return "en"
