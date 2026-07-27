#!/usr/bin/env python3
"""Tests for the standalone Stylus UserCSS exporter."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "theme-stylus"
LOADER = SourceFileLoader("theme_stylus_cli", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
if SPEC is None:
    raise RuntimeError(f"could not load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


class StylusExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = {
            "dark": True,
            "roles": {
                "bg": "#1e1e2e",
                "bg_alt": "#181825",
                "text": "#cdd6f4",
                "text_dim": "#a6adc8",
                "focus": "#cba6f7",
                "border_normal": "#313244",
                "accent": "#cba6f7",
                "accent2": "#89b4fa",
                "urgent": "#f38ba8",
                "sel_bg": "#cba6f7",
                "sel_fg": "#1e1e2e",
            },
        }

    def test_soft_profile_has_metadata_and_semantic_variables(self) -> None:
        css = MODULE.render_usercss("catppuccin_mocha", self.data, "soft")

        self.assertIn("==UserStyle==", css)
        self.assertIn("Theme Engine — catppuccin_mocha (soft)", css)
        self.assertIn("--theme-engine-bg: #1e1e2e", css)
        self.assertIn("--theme-engine-accent: #cba6f7", css)
        self.assertIn("color-scheme: dark", css)
        self.assertNotIn("Full profile", css)

    def test_full_profile_adds_surface_rules(self) -> None:
        css = MODULE.render_usercss("catppuccin_mocha", self.data, "full")

        self.assertIn("Full profile", css)
        self.assertIn(":where(html, body)", css)
        self.assertIn(":where(button, input, textarea, select, option)", css)
        self.assertNotIn("filter:", css)

    def test_light_theme_sets_light_color_scheme(self) -> None:
        data = {**self.data, "dark": False}
        css = MODULE.render_usercss("latte", data, "soft")
        self.assertIn("color-scheme: light", css)

    def test_invalid_role_uses_fallback(self) -> None:
        data = {
            "dark": True,
            "roles": {
                "bg": "#101010",
                "bg_alt": "#202020",
                "text": "not-a-color",
                "ansi_br_white": "#eeeeee",
                "accent": "#336699",
            },
        }
        css = MODULE.render_usercss("fixture", data, "soft")
        self.assertIn("--theme-engine-text: #eeeeee", css)

    def test_atomic_writer_replaces_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "theme.user.css"
            MODULE.atomic_write(destination, "first\n")
            MODULE.atomic_write(destination, "second\n")
            self.assertEqual(destination.read_text(encoding="utf-8"), "second\n")
            self.assertEqual(list(destination.parent.glob("theme.user.css.*")), [])

    def test_auto_browser_prefers_native_floorp(self) -> None:
        installed = {
            "floorp": "/usr/bin/floorp",
            "flatpak": "/usr/bin/flatpak",
            "firefox": "/usr/bin/firefox",
            "xdg-open": "/usr/bin/xdg-open",
        }
        with patch.object(MODULE.shutil, "which", side_effect=installed.get):
            commands = MODULE.browser_commands("auto")

        self.assertEqual(commands[0], ("Floorp", ["/usr/bin/floorp"]))
        self.assertEqual(
            commands[1],
            ("Floorp Flatpak", ["/usr/bin/flatpak", "run", MODULE.FLOORP_FLATPAK_ID]),
        )
        self.assertEqual(commands[2], ("Firefox", ["/usr/bin/firefox"]))

    def test_floorp_browser_does_not_add_firefox_fallback(self) -> None:
        installed = {
            "flatpak": "/usr/bin/flatpak",
            "firefox": "/usr/bin/firefox",
        }
        with patch.object(MODULE.shutil, "which", side_effect=installed.get):
            commands = MODULE.browser_commands("floorp")

        self.assertEqual(
            commands,
            [("Floorp Flatpak", ["/usr/bin/flatpak", "run", MODULE.FLOORP_FLATPAK_ID])],
        )


if __name__ == "__main__":
    unittest.main()