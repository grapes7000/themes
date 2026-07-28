#!/usr/bin/env python3
"""Runtime bridge between the stable legacy generator and Theme Studio overrides."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from theme_components import apply_all
from theme_schema import dump_json, ensure_theme_schema, safe_theme_name
import theme_waybar

CFG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
THEME_DIR = CFG / "hypr" / "themes"
ACTIVE_FILE = CFG / "hypr" / "generated" / ".active"
PREVIEW_NAME = "_theme_studio_preview"


def active_theme() -> str | None:
    try:
        value = ACTIVE_FILE.read_text(encoding="utf-8").strip()
        return value or None
    except OSError:
        return None


def legacy_command() -> list[str] | None:
    explicit = os.environ.get("THEME_LEGACY_COMMAND")
    if explicit:
        return explicit.split()
    found = shutil.which("theme-legacy")
    if found:
        return [found]
    sibling = Path(__file__).resolve().with_name("theme-legacy")
    if sibling.exists():
        return [str(sibling)]
    # Development checkout: original engine is named bin/theme while the studio
    # entry point is bin/theme-studio.
    source = Path(__file__).resolve().with_name("theme")
    if source.exists() and source.name != Path(sys.argv[0]).name:
        return [str(source)]
    return None


def load_theme(name: str) -> dict[str, Any]:
    path = THEME_DIR / f"{safe_theme_name(name)}.json"
    return ensure_theme_schema(json.loads(path.read_text(encoding="utf-8")))


def write_preview(data: dict[str, Any]) -> Path:
    THEME_DIR.mkdir(parents=True, exist_ok=True)
    path = THEME_DIR / f"{PREVIEW_NAME}.json"
    fd, tmp_name = tempfile.mkstemp(prefix=".preview-", dir=str(THEME_DIR), text=True)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(dump_json(ensure_theme_schema(data)))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    return path


def cleanup_preview() -> None:
    (THEME_DIR / f"{PREVIEW_NAME}.json").unlink(missing_ok=True)


def _run_legacy(name: str) -> tuple[bool, str]:
    command = legacy_command()
    if not command:
        return False, "legacy generator not found; applied Studio-managed components only"
    proc = subprocess.run(command + [name], text=True, capture_output=True)
    message = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode == 0, message


def apply_studio_overrides(name: str, *, restart_waybar: bool = False,
                           components: list[str] | None = None) -> dict[str, Any]:
    """Apply only Studio-managed component layers after a legacy subcommand."""
    theme = load_theme(name)
    component_result = apply_all(theme, components)
    waybar_paths = theme_waybar.apply(theme, restart=restart_waybar)
    return {
        "name": name,
        "components": component_result,
        "waybar": {k: str(v) for k, v in waybar_paths.items()},
    }


def apply_theme(name: str, *, restart_waybar: bool = False,
                components: list[str] | None = None) -> dict[str, Any]:
    theme = load_theme(name)
    legacy_ok, legacy_message = _run_legacy(name)
    component_result = apply_all(theme, components)
    waybar_paths = theme_waybar.apply(theme, restart=restart_waybar)
    ACTIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.write_text(name + "\n", encoding="utf-8")
    return {
        "name": name,
        "legacy_ok": legacy_ok,
        "legacy_message": legacy_message,
        "components": component_result,
        "waybar": {k: str(v) for k, v in waybar_paths.items()},
    }


def preview_theme(data: dict[str, Any], reason: str = "Preview") -> dict[str, Any]:
    write_preview(data)
    result = apply_theme(PREVIEW_NAME)
    result["reason"] = reason
    return result


def restore_theme(name: str) -> dict[str, Any]:
    cleanup_preview()
    return apply_theme(name)


def apply_saved_theme(name: str) -> dict[str, Any]:
    cleanup_preview()
    return apply_theme(name, restart_waybar=False)
