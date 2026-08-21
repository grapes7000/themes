#!/usr/bin/env python3
"""Semantic UI-style profiles for Qt/application consumers.

Color themes answer "what does accent/error/background mean?". UI styles answer
"how should controls be shaped, spaced and composed?". The two axes are
independent and are published as separate generated contracts.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

HOME = Path(os.path.expanduser("~"))
CFG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))
PROFILE_DIR = CFG / "theme-engine" / "ui-styles"
STATE_FILE = CFG / "theme-engine" / "ui-style"
CONTRACT_FILE = CFG / "theme-engine" / "generated" / "ui-style.json"
DEFAULT_PROFILE = "precision"


def _atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".ui-style-", suffix=".tmp", dir=path.parent)
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
    if not PROFILE_DIR.exists():
        return []
    return sorted(p.stem for p in PROFILE_DIR.glob("*.json"))


def load_profile(name: str) -> dict:
    path = PROFILE_DIR / f"{name}.json"
    if not path.exists():
        raise ValueError(f"unknown UI style '{name}'. Available: {', '.join(list_profiles())}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError(f"UI style '{name}' uses an unsupported schema")
    if data.get("name") != name:
        raise ValueError(f"UI style '{name}' has a mismatched name field")
    if not isinstance(data.get("metrics"), dict) or not isinstance(data.get("patterns"), dict):
        raise ValueError(f"UI style '{name}' is missing metrics/patterns")
    return data


def override_name() -> str | None:
    try:
        value = STATE_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def set_override(name: str | None) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text((name or "auto") + "\n", encoding="utf-8")


def theme_profile(theme: dict | None) -> str | None:
    if not isinstance(theme, dict):
        return None
    value = theme.get("ui_style")
    return value if isinstance(value, str) and value else None


def resolved_name(theme: dict | None = None) -> tuple[str, str]:
    override = override_name()
    if override and override != "auto":
        return override, "override"
    linked = theme_profile(theme)
    if linked:
        return linked, "theme"
    return DEFAULT_PROFILE, "default"


def publish(theme: dict | None = None, theme_name: str | None = None) -> dict:
    name, source = resolved_name(theme)
    profile = load_profile(name)
    contract = dict(profile)
    contract["resolved_from"] = source
    contract["theme"] = theme_name or (theme.get("name") if isinstance(theme, dict) else None)
    _atomic_json(CONTRACT_FILE, contract)
    return contract


def current(theme: dict | None = None) -> str:
    try:
        name, source = resolved_name(theme)
        return f"{name} ({source})"
    except Exception:
        return "(unavailable)"


def command(args: list[str], theme: dict | None = None, theme_name: str | None = None) -> int:
    if args and args[0] in ("-l", "--list"):
        print("\n".join(list_profiles()))
        return 0
    if not args:
        print(current(theme))
        return 0
    name = args[0]
    if name == "auto":
        set_override(None)
        result = publish(theme, theme_name)
        print(f"ui style -> {result['name']} ({result['resolved_from']})")
        return 0
    load_profile(name)
    set_override(name)
    result = publish(theme, theme_name)
    print(f"ui style -> {result['name']} (override)")
    return 0
