from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = (ROOT / "install.sh").read_text(encoding="utf-8")


def test_installer_has_target_presets() -> None:
    assert "--targets auto|terminal|full" in INSTALLER
    assert "TARGET_MODE=auto" in INSTALLER
    assert "terminal)" in INSTALLER
    assert "full)" in INSTALLER


def test_installer_does_not_own_shell_framework_or_packages() -> None:
    lowered = INSTALLER.lower()
    assert "ohmyzsh/ohmyzsh" not in lowered
    assert "raw.githubusercontent.com/ohmyzsh" not in lowered
    assert "sudo pacman -s" not in lowered
    assert "apt-get install" not in lowered
    assert "dnf install" not in lowered


def test_terminal_mode_contains_only_portable_targets() -> None:
    terminal_function = INSTALLER.split("emit_terminal_targets() {", 1)[1].split("}\n", 1)[0]
    for target in ("kitty", "starship", "nvim", "zsh"):
        assert target in terminal_function
    for target in ("hypr", "waybar", "wallpaper", "wofi", "rofi", "dunst", "hyprlock", "homepage"):
        assert target not in terminal_function
