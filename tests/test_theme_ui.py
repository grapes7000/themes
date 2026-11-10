import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

import theme_runtime
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
        self.original_paths = (
            theme_ui.PROFILE_DIR,
            theme_ui.STATE_FILE,
            theme_ui.CONTRACT_FILE,
        )
        _configure(self.root)

    def tearDown(self):
        theme_ui.PROFILE_DIR, theme_ui.STATE_FILE, theme_ui.CONTRACT_FILE = (
            self.original_paths
        )
        self.tempdir.cleanup()

    def test_theme_profile_is_used_in_auto_mode(self):
        theme_ui.set_override(None)
        self.assertEqual(
            theme_ui.resolved_name({"ui_style": "win95"}), ("win95", "theme")
        )

    def test_explicit_override_wins_and_publishes_contract(self):
        theme_ui.set_override("legacy")
        contract = theme_ui.publish(
            {"name": "graphite", "ui_style": "precision"}, "graphite"
        )
        self.assertEqual(contract["resolved_from"], "override")
        self.assertEqual(
            json.loads(theme_ui.CONTRACT_FILE.read_text())["name"], "legacy"
        )

    def test_theme_style_overrides_are_published_without_changing_profile(self):
        profile = {
            **_profile("precision"),
            "metrics": {"radius_surface": 4},
            "patterns": {"motion": "restrained"},
        }
        (theme_ui.PROFILE_DIR / "precision.json").write_text(json.dumps(profile))
        theme = {
            "ui_style_overrides": {
                "metrics": {"radius_surface": 19},
                "patterns": {"motion": "playful"},
            }
        }
        contract = theme_ui.publish(theme)
        self.assertEqual(contract["metrics"]["radius_surface"], 19)
        self.assertEqual(contract["patterns"]["motion"], "playful")
        self.assertEqual(theme_ui.load_profile("precision"), profile)

    def test_invalid_profile_name_cannot_escape_profile_directory(self):
        with self.assertRaises(ValueError):
            theme_ui.load_profile("../outside")

    def test_custom_profile_takes_precedence_over_bundled(self):
        bundled = theme_ui.PROFILE_DIR / "bundled"
        custom = theme_ui.PROFILE_DIR / "custom"
        bundled.mkdir()
        custom.mkdir()
        (bundled / "legacy.json").write_text(
            json.dumps({**_profile("legacy"), "metrics": {"radius": 1}})
        )
        (custom / "legacy.json").write_text(
            json.dumps({**_profile("legacy"), "metrics": {"radius": 9}})
        )
        self.assertEqual(theme_ui.load_profile("legacy")["metrics"]["radius"], 9)

    def test_create_custom_profile_does_not_replace_existing_style(self):
        path = theme_ui.save_custom_profile("mine", "precision")
        self.assertEqual(json.loads(path.read_text())["name"], "mine")
        with self.assertRaises(ValueError):
            theme_ui.save_custom_profile("mine", "legacy")

    def test_compatibility_command_selects_the_same_profile_as_theme_ui(self):
        cfg = self.root / "config"
        profiles = cfg / "theme-engine" / "ui-styles" / "bundled"
        profiles.mkdir(parents=True)
        (profiles / "legacy.json").write_text(json.dumps(_profile("legacy")))
        result = subprocess.run(
            [sys.executable, str(ROOT / "bin" / "ui-style"), "legacy"],
            env={**os.environ, "XDG_CONFIG_HOME": str(cfg)},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (cfg / "theme-engine" / "ui-style").read_text().strip(), "legacy"
        )
        self.assertEqual(
            json.loads(
                (cfg / "theme-engine" / "generated" / "ui-style.json").read_text()
            )["name"],
            "legacy",
        )

    def test_saved_theme_application_publishes_its_ui_style(self):
        theme = {"name": "example", "ui_style": "win95"}
        with (
            patch.object(theme_runtime, "load_theme", return_value=theme),
            patch.object(theme_runtime, "_run_legacy", return_value=(True, "")),
            patch.object(theme_runtime, "_write_live_contract"),
            patch.object(
                theme_runtime, "_sync_semantic_wallpaper", return_value=(False, "")
            ),
            patch.object(theme_runtime, "apply_all", return_value={}),
            patch.object(theme_runtime, "_sync_noctalia", return_value=(False, "")),
            patch.object(theme_runtime, "_reload_hyprland", return_value=(False, "")),
            patch.object(
                theme_runtime, "_apply_static_wallpaper", return_value=(False, "")
            ),
            patch.object(
                theme_runtime, "_sync_starship_runtime", return_value=(False, "")
            ),
            patch.object(theme_runtime, "ACTIVE_FILE", self.root / "active"),
        ):
            theme_runtime.apply_theme("example")
        self.assertEqual(
            json.loads(theme_ui.CONTRACT_FILE.read_text())["name"], "win95"
        )
