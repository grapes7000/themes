#!/usr/bin/env python3
"""Tests for the standalone pywal/pywalfox compatibility exporter."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "theme-pywalfox"
LOADER = SourceFileLoader("theme_pywalfox_cli", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
if SPEC is None:
    raise RuntimeError(f"could not load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


class PywalfoxExportTests(unittest.TestCase):
    def test_payload_contains_required_pywalfox_fields(self) -> None:
        roles = {
            "bg": "#101010",
            "bg_alt": "#202020",
            "text": "#f0f0f0",
            "text_dim": "#b0b0b0",
            "accent": "#6699cc",
            "accent2": "#66cc99",
            "urgent": "#cc6666",
            "cursor": "#f0f0f0",
        }
        data = {"roles": roles, "dark": True}
        payload = MODULE.build_payload("fixture", data, Path("/tmp/wallpaper.png"))

        self.assertEqual(payload["wallpaper"], "/tmp/wallpaper.png")
        self.assertEqual(payload["special"]["background"], "#101010")
        self.assertEqual(payload["special"]["foreground"], "#f0f0f0")
        self.assertEqual(list(payload["colors"]), [f"color{i}" for i in range(16)])
        self.assertEqual(len(payload["colors"]), 16)
        self.assertEqual(payload["theme_engine"]["mapping"], "pywalfox-semantic-v1")

    def test_incomplete_theme_receives_deterministic_ansi_fallbacks(self) -> None:
        roles = {
            "bg": "#111111",
            "bg_alt": "#222222",
            "text": "#eeeeee",
            "text_dim": "#aaaaaa",
            "accent": "#336699",
            "accent2": "#669933",
            "urgent": "#993333",
        }
        palette = MODULE.ansi_palette(roles)

        self.assertEqual(len(palette), 16)
        self.assertEqual(palette[0], "#111111")
        self.assertEqual(palette[1], "#993333")
        self.assertEqual(palette[8], "#222222")
        self.assertEqual(palette[15], "#eeeeee")

    def test_explicit_ansi_roles_are_preserved_in_base_palette(self) -> None:
        roles = {
            "bg": "#000000",
            "bg_alt": "#111111",
            "text": "#ffffff",
            "text_dim": "#cccccc",
            "accent": "#123456",
            "accent2": "#234567",
            "urgent": "#ff0000",
            **{key: f"#{index:06x}" for index, key in enumerate(MODULE.ANSI_KEYS)},
        }
        palette = MODULE.ansi_palette(roles)
        self.assertEqual(palette, [f"#{index:06x}" for index in range(16)])

    def test_dark_pywalfox_slots_use_semantic_theme_roles(self) -> None:
        roles = {
            "bg": "#1e1e2e",
            "bg_alt": "#181825",
            "text": "#cdd6f4",
            "text_dim": "#a6adc8",
            "accent": "#cba6f7",
            "accent2": "#89b4fa",
            "urgent": "#f38ba8",
            **{key: f"#{index:06x}" for index, key in enumerate(MODULE.ANSI_KEYS)},
        }
        palette = MODULE.pywalfox_palette(roles, dark=True)

        self.assertEqual(palette[0], "#1e1e2e")
        self.assertEqual(palette[10], "#cba6f7")
        self.assertEqual(palette[13], "#89b4fa")
        self.assertEqual(palette[15], "#cdd6f4")
        self.assertEqual(palette[1], "#000001")

    def test_light_pywalfox_slots_use_semantic_theme_roles(self) -> None:
        roles = {
            "bg": "#eff1f5",
            "bg_alt": "#e6e9ef",
            "text": "#4c4f69",
            "text_dim": "#6c6f85",
            "accent": "#8839ef",
            "accent2": "#1e66f5",
            "urgent": "#d20f39",
            **{key: f"#{index:06x}" for index, key in enumerate(MODULE.ANSI_KEYS)},
        }
        palette = MODULE.pywalfox_palette(roles, dark=False)

        self.assertEqual(palette[0], "#4c4f69")
        self.assertEqual(palette[3], "#8839ef")
        self.assertEqual(palette[5], "#1e66f5")
        self.assertEqual(palette[7], "#eff1f5")
        self.assertEqual(palette[1], "#000001")

    def test_atomic_writer_produces_valid_json(self) -> None:
        payload = {
            "wallpaper": "/tmp/wallpaper.png",
            "colors": {f"color{i}": "#000000" for i in range(16)},
        }
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "wal" / "colors.json"
            MODULE.atomic_write_json(destination, payload)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), payload)
            self.assertEqual(list(destination.parent.glob("colors.*.json")), [])


if __name__ == "__main__":
    unittest.main()
