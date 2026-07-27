#!/usr/bin/env python3
"""Tests for the pywal16 image-to-theme bridge."""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "theme-from-image"
LOADER = SourceFileLoader("theme_from_image_cli", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
if SPEC is None:
    raise RuntimeError(f"could not load {SCRIPT}")
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)


def fixture_payload() -> dict:
    colors = [
        "#101116", "#d35f5f", "#7fb069", "#d5b66f",
        "#719cd6", "#a77bd8", "#62b3b2", "#b7b9c2",
        "#3a3d4b", "#ef7373", "#91c77a", "#ebca7e",
        "#89b4fa", "#cba6f7", "#7fd0cf", "#e6e9ef",
    ]
    return {
        "wallpaper": "/tmp/source.jpg",
        "special": {
            "background": "#101116",
            "foreground": "#e6e9ef",
            "cursor": "#cba6f7",
        },
        "colors": {f"color{i}": color for i, color in enumerate(colors)},
    }


class ThemeFromImageTests(unittest.TestCase):
    def test_theme_mapping_preserves_ansi_and_builds_semantic_roles(self) -> None:
        theme = MODULE.theme_from_pywal(
            "sunset",
            fixture_payload(),
            dark=True,
            wallpaper=Path("/tmp/sunset.png"),
            style={"corner_radius": 12},
            style_source="catppuccin_mocha",
            cols16="darken",
        )

        self.assertTrue(theme["dark"])
        self.assertEqual(theme["style"]["corner_radius"], 12)
        self.assertEqual(theme["roles"]["bg"], "#101116")
        self.assertEqual(theme["roles"]["text"], "#e6e9ef")
        self.assertEqual(theme["roles"]["ansi_blue"], "#719cd6")
        self.assertEqual(theme["roles"]["ansi_br_blue"], "#89b4fa")
        self.assertIn(theme["roles"]["accent"], fixture_payload()["colors"].values())
        self.assertNotEqual(theme["roles"]["accent"], theme["roles"]["bg"])
        self.assertGreaterEqual(
            MODULE.contrast_ratio(theme["roles"]["sel_fg"], theme["roles"]["sel_bg"]),
            2.0,
        )

    def test_light_theme_sets_light_mode(self) -> None:
        payload = fixture_payload()
        payload["special"]["background"] = "#eff1f5"
        payload["special"]["foreground"] = "#4c4f69"
        payload["colors"]["color0"] = "#4c4f69"
        payload["colors"]["color7"] = "#eff1f5"

        theme = MODULE.theme_from_pywal(
            "light", payload, dark=False, wallpaper=Path("/tmp/light.png")
        )
        self.assertFalse(theme["dark"])
        self.assertEqual(theme["roles"]["bg"], "#eff1f5")
        self.assertEqual(theme["roles"]["text"], "#4c4f69")

    def test_invalid_payload_is_rejected(self) -> None:
        payload = fixture_payload()
        payload["colors"]["color12"] = "bad"
        with self.assertRaisesRegex(ValueError, "color12"):
            MODULE.validate_pywal_payload(payload)

    def test_slugify_is_stable(self) -> None:
        self.assertEqual(MODULE.slugify("My Gorgeous Sunset!!"), "my-gorgeous-sunset")

    def test_run_pywal_uses_safe_isolated_flags(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image = root / "image.png"
            image.write_bytes(b"png")
            log = root / "args.json"
            fake = root / "wal"
            payload = fixture_payload()
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, pathlib, sys\n"
                "if '--help' in sys.argv:\n"
                "    print('--cols16 --out-dir --contrast')\n"
                "    raise SystemExit(0)\n"
                "args = sys.argv[1:]\n"
                "pathlib.Path(os.environ['ARG_LOG']).write_text(json.dumps(args))\n"
                "out = pathlib.Path(args[args.index('--out-dir') + 1])\n"
                "out.mkdir(parents=True, exist_ok=True)\n"
                f"(out / 'colors.json').write_text({json.dumps(json.dumps(payload))})\n",
                encoding="utf-8",
            )
            fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

            with mock.patch.dict(os.environ, {"ARG_LOG": str(log)}):
                result = MODULE.run_pywal(
                    image,
                    wal=str(fake),
                    dark=True,
                    backend="colorthief",
                    cols16="dual",
                    saturate_value=0.3,
                    contrast_value=3.0,
                )

            self.assertEqual(result["special"]["background"], "#101116")
            args = json.loads(log.read_text(encoding="utf-8"))
            for flag in ("-n", "-s", "-t", "-e", "--out-dir", "--cols16"):
                self.assertIn(flag, args)
            self.assertEqual(args[args.index("--backend") + 1], "colorthief")
            self.assertNotIn("-l", args)

    def test_atomic_writer_replaces_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "themes" / "x.json"
            MODULE.atomic_write_json(path, {"first": 1})
            MODULE.atomic_write_json(path, {"second": 2})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"second": 2})
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_png_copy_is_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.png"
            source.write_bytes(b"fake-png")
            destination = root / "wallpapers" / "theme.png"
            MODULE.copy_wallpaper_png(source, destination)
            self.assertEqual(destination.read_bytes(), b"fake-png")


if __name__ == "__main__":
    unittest.main()
