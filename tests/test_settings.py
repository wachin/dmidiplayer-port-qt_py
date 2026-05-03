from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dmidiplayer_py.settings import AppSettings


class AppSettingsTest(unittest.TestCase):
    def test_last_folder_is_saved_in_app_data_settings_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir, "appdata")
            folder = Path(tmpdir, "music")
            fallback = Path(tmpdir)
            folder.mkdir()

            settings = AppSettings(base_dir)
            settings.set_last_folder(folder)
            restored = AppSettings(base_dir)

            self.assertEqual(restored.last_folder(fallback), folder)
            self.assertTrue((base_dir / "settings.ini").exists())

    def test_missing_last_folder_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir, "appdata")
            fallback = Path(tmpdir)

            settings = AppSettings(base_dir)

            self.assertEqual(settings.last_folder(fallback), fallback)

    def test_unwritable_app_data_falls_back_to_temp(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            blocking_file = Path(tmpdir, "not-a-directory")
            blocking_file.write_text("")

            settings = AppSettings(blocking_file)

            self.assertNotEqual(settings.base_dir, blocking_file)
            self.assertTrue(settings.path.exists() or settings.base_dir.exists())


if __name__ == "__main__":
    unittest.main()
