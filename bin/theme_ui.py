"""Resolve and publish semantic UI-style profiles for application consumers."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

HOME = Path.home()
CFG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))
PROFILE_DIR = CFG / "theme-engine" / "ui-styles"
STATE_FILE = CFG / "theme-engine" / "ui-style"
CONTRACT_FILE = CFG / "theme-engine" / "generated" / "ui-style.json"
DEFAULT_PROFILE = "precision"
SHELL_MOTION_METRICS = frozenset(
    {
        "motion_fast_ms",
        "motion_normal_ms",
        "motion_hover_percent",
        "motion_press_percent",
        "motion_overshoot_percent",
    }
)
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _valid_name(name: str) -> bool:
    return bool(NAME_RE.fullmatch(name))


def _atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=".ui-style-", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def list_profiles() -> list[str]:
    directories = (PROFILE_DIR, PROFILE_DIR / "bundled", PROFILE_DIR / "custom")
    return sorted(
        {
            path.stem
            for directory in directories
            for path in directory.glob("*.json")
            if _valid_name(path.stem)
        }
    )


def load_profile(name: str) -> dict[str, Any]:
    if not _valid_name(name):
        raise ValueError(
            "UI style names may contain only lowercase letters, numbers, _ and -"
        )
    candidates = (
        PROFILE_DIR / "custom" / f"{name}.json",
        PROFILE_DIR / "bundled" / f"{name}.json",
        PROFILE_DIR / f"{name}.json",
    )
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        available = ", ".join(list_profiles()) or "(none installed)"
        raise ValueError(f"unknown UI style '{name}'. Available: {available}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("name") != name:
        raise ValueError(f"UI style '{name}' has an unsupported schema")
    if not isinstance(data.get("metrics"), dict) or not isinstance(
        data.get("patterns"), dict
    ):
        raise TypeError(f"UI style '{name}' is missing metrics or patterns")
    return data


def save_custom_profile(name: str, base: str) -> Path:
    if not _valid_name(name):
        raise ValueError(
            "UI style names may contain only lowercase letters, numbers, _ and -"
        )
    if name in list_profiles():
        raise ValueError(f"UI style '{name}' already exists")
    data = dict(load_profile(base))
    data["name"] = name
    data["description"] = f"Custom style based on {base}"
    path = PROFILE_DIR / "custom" / f"{name}.json"
    _atomic_json(path, data)
    return path


def override_name() -> str | None:
    try:
        value = STATE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value if value != "auto" and _valid_name(value) else None


def set_override(name: str | None) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text((name or "auto") + "\n", encoding="utf-8")


def theme_profile(theme: dict[str, Any] | None) -> str | None:
    value = theme.get("ui_style") if isinstance(theme, dict) else None
    return value if isinstance(value, str) and _valid_name(value) else None


def resolved_name(theme: dict[str, Any] | None = None) -> tuple[str, str]:
    override = override_name()
    if override:
        return override, "override"
    linked = theme_profile(theme)
    if linked:
        return linked, "theme"
    return DEFAULT_PROFILE, "default"


def publish(
    theme: dict[str, Any] | None = None, theme_name: str | None = None
) -> dict[str, Any]:
    name, source = resolved_name(theme)
    contract = dict(load_profile(name))
    overrides = theme.get("ui_style_overrides", {}) if isinstance(theme, dict) else {}
    for section in ("metrics", "patterns"):
        values = overrides.get(section, {}) if isinstance(overrides, dict) else {}
        if isinstance(values, dict):
            contract[section] = {
                **contract[section],
                **{
                    key: value
                    for key, value in values.items()
                    if key in contract[section]
                    or (section == "metrics" and key in SHELL_MOTION_METRICS)
                },
            }
    contract["resolved_from"] = source
    contract["theme"] = theme_name or (
        theme.get("name") if isinstance(theme, dict) else None
    )
    _atomic_json(CONTRACT_FILE, contract)
    return contract


def command(
    args: list[str], theme: dict[str, Any] | None = None, theme_name: str | None = None
) -> int:
    if args and args[0] in ("-l", "--list"):
        print("\n".join(list_profiles()))
        return 0
    if len(args) > 1:
        raise ValueError("usage: theme ui [--list|auto|PROFILE]")
    if not args:
        name, source = resolved_name(theme)
        print(f"{name} ({source})")
        return 0
    name = args[0]
    if name == "auto":
        set_override(None)
    else:
        load_profile(name)
        set_override(name)
    result = publish(theme, theme_name)
    print(f"ui style -> {result['name']} ({result['resolved_from']})")
    return 0
