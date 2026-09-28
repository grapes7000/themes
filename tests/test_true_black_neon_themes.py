"""Contract checks for the true-black, high-saturation neon theme family."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME_NAMES = ("rgb-neon", "arcade-neon", "acid-neon", "y2k-neon")
ANSI_HUES = ("red", "green", "yellow", "blue", "magenta", "cyan")


def _rgb(value):
    value = value.removeprefix("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _load_theme(name):
    return json.loads((ROOT / "themes" / f"{name}.json").read_text(encoding="utf-8"))


def test_true_black_neon_theme_family_is_complete():
    for name in THEME_NAMES:
        theme = _load_theme(name)
        roles = theme["roles"]

        assert theme["name"] == name
        assert theme["dark"] is True
        assert roles["bg"] == "#000000"
        assert theme["style"]["opacity"] == 1.0
        assert theme["style"]["opacity_inactive"] == 1.0
        assert str(theme["style"]["blur_on"]).lower() == "false"

        ansi_values = [roles[f"ansi_{color}"] for color in ANSI_HUES]
        bright_values = [roles[f"ansi_br_{color}"] for color in ANSI_HUES]
        assert len(set(ansi_values + bright_values)) == 12

        for value in ansi_values + bright_values:
            rgb = _rgb(value)
            assert max(rgb) >= 198
            assert max(rgb) - min(rgb) >= 180


def test_true_black_neon_text_is_bright_neutral():
    for name in THEME_NAMES:
        red, green, blue = _rgb(_load_theme(name)["roles"]["text"])
        assert min(red, green, blue) >= 224
        assert max(red, green, blue) - min(red, green, blue) <= 32
