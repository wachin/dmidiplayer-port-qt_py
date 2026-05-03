from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from dmidiplayer_py.i18n import install_translator


class I18nTest(unittest.TestCase):
    def test_english_is_source_language(self) -> None:
        app = QApplication.instance() or QApplication([])

        self.assertEqual(install_translator(app, "en"), "en")

    def test_missing_translation_falls_back_to_english(self) -> None:
        app = QApplication.instance() or QApplication([])

        self.assertEqual(install_translator(app, "zz"), "en")


if __name__ == "__main__":
    unittest.main()
