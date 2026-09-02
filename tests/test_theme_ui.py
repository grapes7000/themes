import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

import theme_ui


def _profile(name: str) -> dict:
    return {"schema_version": 1, "name": name, "metrics": {}, "patterns": {}}


def _configure(tmp_path: Path):
    profiles = tmp_path / "ui-styles"
    profiles.mkdir()
    for name in ("precision", "legacy", "win95"):
        (profiles / f"{name}.json").write_text(json.dumps(_profile(name)))
    theme_ui.PROFILE_DIR = profiles
    theme_ui.STATE_FILE = tmp_path / "ui-style"
    theme_ui.CONTRACT_FILE = tmp_path / "generated" / "ui-style.json"


class ThemeUiTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.original_paths = theme_ui.PROFILE_DIR, theme_ui.STATE_FILE, theme_ui.CONTRACT_FILE
        _configure(self.root)

    def tearDown(self):
        theme_ui.PROFILE_DIR, theme_ui.STATE_FILE, theme_ui.CONTRACT_FILE = self.original_paths
        self.tempdir.cleanup()

    def test_theme_profile_is_used_in_auto_mode(self):
        theme_ui.set_override(None)
        self.assertEqual(theme_ui.resolved_name({"ui_style": "win95"}), ("win95", "theme"))

    def test_explicit_override_wins_and_publishes_contract(self):
        theme_ui.set_override("legacy")
        contract = theme_ui.publish({"name": "graphite", "ui_style": "precision"}, "graphite")
        self.assertEqual(contract["resolved_from"], "override")
        self.assertEqual(json.loads(theme_ui.CONTRACT_FILE.read_text())["name"], "legacy")

    def test_invalid_profile_name_cannot_escape_profile_directory(self):
        with self.assertRaises(ValueError):
            theme_ui.load_profile("../outside")
