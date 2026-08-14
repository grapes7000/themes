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
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
THEME_DIR = CFG / "hypr" / "themes"
ACTIVE_FILE = CFG / "hypr" / "generated" / ".active"
TARGETS_FILE = CFG / "theme-engine" / "targets.conf"
RENDER_ROOT = CACHE / "theme-engine" / "wallpapers"
PREVIEW_NAME = "_theme_studio_preview"


def active_theme() -> str | None:
    try:
        value = ACTIVE_FILE.read_text(encoding="utf-8").strip()
        return value or None
    except OSError:
        return None


def enabled_targets() -> set[str] | None:
    if not TARGETS_FILE.exists():
        return None
    targets: set[str] = set()
    for raw in TARGETS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            targets.add(line.split("=", 1)[0].strip())
    return targets


def target_enabled(name: str) -> bool:
    targets = enabled_targets()
    return True if targets is None else name in targets


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
    source = Path(__file__).resolve().with_name("theme")
    if source.exists() and source.name != Path(sys.argv[0]).name:
        return [str(source)]
    return None


def wallgen_command() -> list[str] | None:
    explicit = os.environ.get("THEME_WALLGEN_COMMAND")
    if explicit:
        return explicit.split()
    found = shutil.which("wallgen")
    if found:
        return [found]
    sibling = Path(__file__).resolve().with_name("wallgen")
    if sibling.exists():
        return [str(sibling)]
    return None


def noctalia_command() -> list[str] | None:
    explicit = os.environ.get("THEME_NOCTALIA_COMMAND")
    if explicit:
        return explicit.split()
    found = shutil.which("theme-noctalia")
    if found:
        return [found]
    sibling = Path(__file__).resolve().with_name("theme-noctalia")
    if sibling.exists():
        return [str(sibling)]
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


def _atomic_symlink(target: Path, link: Path) -> None:
    """Atomically point *link* at *target*, replacing the previous link/file."""
    target = target.expanduser().resolve()
    link.parent.mkdir(parents=True, exist_ok=True)
    temporary = link.with_name(f".{link.name}.{os.getpid()}.tmp")
    temporary.unlink(missing_ok=True)
    try:
        os.symlink(str(target), temporary)
        os.replace(temporary, link)
    finally:
        temporary.unlink(missing_ok=True)


def _publish_current_wallpaper(rendered: Path) -> tuple[Path, Path]:
    """Publish stable links for consumers that should follow the active wallpaper."""
    rendered = rendered.expanduser().resolve()
    if not rendered.is_file():
        raise OSError(f"rendered wallpaper does not exist: {rendered}")
    current = RENDER_ROOT / "current.png"
    homepage = CFG / "quickshell" / "homepage-images" / "theme-wallpaper.png"
    _atomic_symlink(rendered, current)
    _atomic_symlink(current, homepage)
    return current, homepage


def _sync_semantic_wallpaper(name: str) -> tuple[bool, str]:
    if name == PREVIEW_NAME or not target_enabled("wallpaper"):
        return False, ""
    command = wallgen_command()
    if not command:
        return False, ""
    proc = subprocess.run(command + ["semantic", "apply", name, "--set"], text=True, capture_output=True)
    message = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0:
        return False, message
    if message:
        rendered = Path(message.splitlines()[-1].strip())
        try:
            _publish_current_wallpaper(rendered)
        except OSError as exc:
            return False, f"{message}\ncurrent wallpaper link: {exc}"
    return True, message


def _sync_noctalia(name: str) -> tuple[bool, str]:
    command = noctalia_command()
    if not command:
        return False, ""
    proc = subprocess.run(command + ["apply", name], text=True, capture_output=True)
    message = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode == 0, message


def _apply_waybar(theme: dict[str, Any], *, restart: bool) -> dict[str, Path]:
    if not target_enabled("waybar"):
        return {}
    return theme_waybar.apply(theme, restart=restart)


def apply_studio_overrides(name: str, *, restart_waybar: bool = False, components: list[str] | None = None) -> dict[str, Any]:
    theme = load_theme(name)
    component_result = apply_all(theme, components)
    waybar_paths = _apply_waybar(theme, restart=restart_waybar)
    return {"name": name, "components": component_result, "waybar": {k: str(v) for k, v in waybar_paths.items()}}


def apply_theme(name: str, *, restart_waybar: bool = False, components: list[str] | None = None) -> dict[str, Any]:
    theme = load_theme(name)
    legacy_ok, legacy_message = _run_legacy(name)
    wallpaper_ok, wallpaper_message = _sync_semantic_wallpaper(name)
    component_result = apply_all(theme, components)
    waybar_paths = _apply_waybar(theme, restart=restart_waybar)
    noctalia_ok, noctalia_message = _sync_noctalia(name)
    ACTIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.write_text(name + "\n", encoding="utf-8")
    return {
        "name": name,
        "legacy_ok": legacy_ok,
        "legacy_message": legacy_message,
        "wallpaper_ok": wallpaper_ok,
        "wallpaper_message": wallpaper_message,
        "noctalia_ok": noctalia_ok,
        "noctalia_message": noctalia_message,
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
