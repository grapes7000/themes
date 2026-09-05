#!/usr/bin/env python3
"""Runtime bridge between the stable legacy generator and Theme Studio overrides."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

from theme_components import apply_all
from theme_schema import dump_json, ensure_theme_schema, safe_theme_name

CFG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
THEME_DIR = CFG / "hypr" / "themes"
ACTIVE_FILE = CFG / "hypr" / "generated" / ".active"
TARGETS_FILE = CFG / "theme-engine" / "targets.conf"
RENDER_ROOT = CACHE / "theme-engine" / "wallpapers"
# This name is passed through ``safe_theme_name()`` when the preview is loaded.
# Do not begin it with punctuation: the sanitizer strips a leading underscore,
# which previously made the writer and reader disagree on the file path.
PREVIEW_NAME = "theme_studio_preview"
LEGACY_PREVIEW_NAME = "_theme_studio_preview"


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
    for name in (PREVIEW_NAME, LEGACY_PREVIEW_NAME):
        (THEME_DIR / f"{name}.json").unlink(missing_ok=True)


def _run_legacy(name: str) -> tuple[bool, str]:
    command = legacy_command()
    if not command:
        return False, "legacy generator not found"
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
    static = CFG / "hypr" / "wallpapers" / f"{name}.png"
    if static.is_file():
        return False, "static wallpaper selected"
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


def _reload_hyprland() -> tuple[bool, str]:
    """Reload the final generated Hyprland config and stop hiding failures."""
    if not target_enabled("hypr"):
        return False, ""
    hyprctl = shutil.which("hyprctl")
    if not hyprctl:
        return False, "hyprctl not found"
    if not os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return False, "not in a Hyprland session"
    proc = subprocess.run([hyprctl, "reload"], text=True, capture_output=True)
    message = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode != 0:
        raise RuntimeError(f"Hyprland reload failed: {message or f'exit {proc.returncode}'}")
    return True, message


def _hyprpaper_monitors(hyprctl: str) -> list[str]:
    """Return connected output names without making wallpaper selection implicit."""
    proc = subprocess.run([hyprctl, "monitors", "-j"], text=True, capture_output=True)
    if proc.returncode:
        return []
    try:
        monitors = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    return [item["name"] for item in monitors if isinstance(item, dict) and item.get("name")]


def _ensure_hyprpaper(hyprctl: str) -> tuple[bool, str]:
    """Start Hyprpaper on demand and wait briefly for its IPC socket."""
    probe = [hyprctl, "hyprpaper", "listactive"]
    if subprocess.run(probe, text=True, capture_output=True).returncode == 0:
        return True, ""
    command = shutil.which("hyprpaper")
    if not command:
        return False, "hyprpaper is not installed"
    try:
        subprocess.Popen([command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        return False, f"could not start hyprpaper: {exc}"
    for _ in range(20):
        time.sleep(0.1)
        if subprocess.run(probe, text=True, capture_output=True).returncode == 0:
            return True, ""
    return False, "hyprpaper did not create its IPC socket"


def apply_wallpaper_path(path: Path | str) -> str:
    """Apply an explicit user-selected wallpaper without altering theme bindings."""
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    hyprctl = shutil.which("hyprctl")
    if not hyprctl or not os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        raise RuntimeError("not in a Hyprland session or hyprctl is unavailable")
    ready, message = _ensure_hyprpaper(hyprctl)
    if not ready:
        raise RuntimeError(f"hyprpaper is unavailable: {message}")
    monitors = _hyprpaper_monitors(hyprctl) or [""]
    for monitor in monitors:
        proc = subprocess.run(
            [hyprctl, "hyprpaper", "wallpaper", f"{monitor},{path},cover"],
            text=True, capture_output=True,
        )
        message = (proc.stdout or proc.stderr or "").strip()
        if proc.returncode != 0:
            label = monitor or "fallback"
            raise RuntimeError(f"hyprpaper live switch failed for {label}: {message or f'exit {proc.returncode}'}")
    _publish_current_wallpaper(path)
    return ", ".join(monitors) + ": " + str(path)


def _apply_static_wallpaper(name: str) -> tuple[bool, str]:
    """Apply a theme's bound wallpaper, if it has one and the target is enabled."""
    if name == PREVIEW_NAME or not target_enabled("wallpaper"):
        return False, ""
    path = CFG / "hypr" / "wallpapers" / f"{name}.png"
    if not path.is_file():
        return False, ""
    return True, apply_wallpaper_path(path)


def _starship_color(key: str, roles: dict[str, Any]) -> str:
    """Map common palette names onto the active theme roles."""
    k = key.lower()
    exact = {
        "bg": roles["bg"],
        "background": roles["bg"],
        "surface": roles.get("bg_alt", roles["bg"]),
        "fg": roles["text"],
        "foreground": roles["text"],
        "muted": roles.get("text_dim", roles["text"]),
        "accent": roles["accent"],
        "accent2": roles.get("accent2", roles["accent"]),
        "edge": roles.get("text_dim", roles["text"]),
        "urgent": roles.get("urgent", roles["accent"]),
        "warn": roles.get("ansi_yellow", roles.get("warning", roles["accent"])),
    }
    if k in exact:
        return exact[k]

    def has(*words: str) -> bool:
        return any(word in k for word in words)

    if has("deep", "dark", "back", "base", "night"):
        return roles.get("bg_alt", roles["bg"])
    if has("text", "white", "cream", "snow"):
        return roles["text"]
    if has("grey", "gray", "dim", "muted", "subtle"):
        return roles.get("text_dim", roles["text"])
    if has("red", "hot", "crimson", "error", "urgent", "danger"):
        return roles.get("urgent", roles["accent"])
    if has("lime", "green", "mint"):
        return roles.get("ansi_green", roles.get("accent2", roles["accent"]))
    if has("yellow", "gold", "butter", "amber", "sand", "orange", "peach"):
        return roles.get("ansi_yellow", roles["accent"])
    if has("cyan", "teal", "foam", "aqua"):
        return roles.get("ansi_cyan", roles.get("accent2", roles["accent"]))
    if has("blue", "azure", "sky", "ocean"):
        return roles.get("ansi_blue", roles.get("accent2", roles["accent"]))
    if has("pink", "magenta", "rose", "mauve", "blush"):
        return roles.get("ansi_magenta", roles["accent"])
    if has("purple", "violet", "lavender", "lilac", "grape"):
        return roles["accent"]
    return roles["accent"]


def _sync_starship_runtime(theme: dict[str, Any]) -> tuple[bool, str]:
    """Update the Starship file the current shell actually reads.

    The desktop's managed STARSHIP_CONFIG is a mirror of ~/.config/starship.toml,
    which the canonical theme_starship renderer has already generated. Copying
    that file verbatim preserves prompt geometry, glyphs, and exact palette-role
    assignments. Only unknown/custom STARSHIP_CONFIG paths use palette-only
    recoloring as a compatibility fallback.
    """
    configured = os.environ.get("STARSHIP_CONFIG")
    if not configured or not target_enabled("starship"):
        return False, ""
    target = Path(configured).expanduser()
    default = CFG / "starship.toml"
    managed = CFG / "theme-engine" / "generated" / "starship.toml"

    try:
        if target.resolve() == default.resolve():
            return False, ""
    except OSError:
        pass

    try:
        is_managed = target.resolve() == managed.resolve()
    except OSError:
        is_managed = target == managed

    if is_managed and default.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(default, target)
        return True, str(target)

    if not target.exists():
        if default.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(default, target)
            return True, str(target)
        return False, ""

    roles = theme.get("roles", {})
    if not roles:
        return False, ""

    text = target.read_text(encoding="utf-8")
    out: list[str] = []
    in_palette = False
    changed = False
    pattern = re.compile(r'^(\s*)([A-Za-z0-9_-]+)(\s*=\s*)["\']#?[0-9A-Fa-f]{6}["\'](.*)$')
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[palettes."):
            in_palette = True
        elif stripped.startswith("[") and not stripped.startswith("[palettes."):
            in_palette = False

        if in_palette:
            match = pattern.match(line)
            if match:
                color = _starship_color(match.group(2), roles)
                line = f'{match.group(1)}{match.group(2)}{match.group(3)}"{color}"{match.group(4)}'
                changed = True
        out.append(line)

    if changed:
        target.write_text("\n".join(out) + "\n", encoding="utf-8")
        return True, str(target)
    return False, "no Starship palette block found"


def _sync_noctalia(name: str) -> tuple[bool, str]:
    command = noctalia_command()
    if not command:
        return False, ""
    proc = subprocess.run(command + ["apply", name], text=True, capture_output=True)
    message = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode == 0, message


def apply_studio_overrides(name: str, *, components: list[str] | None = None) -> dict[str, Any]:
    theme = load_theme(name)
    component_result = apply_all(theme, components)
    hypr_ok, hypr_message = _reload_hyprland()
    wallpaper_ok, wallpaper_message = _apply_static_wallpaper(name)
    starship_ok, starship_message = _sync_starship_runtime(theme)
    return {
        "name": name,
        "components": component_result,
        "hyprland_ok": hypr_ok,
        "hyprland_message": hypr_message,
        "wallpaper_ok": wallpaper_ok,
        "wallpaper_message": wallpaper_message,
        "starship_ok": starship_ok,
        "starship_message": starship_message,
    }


def apply_theme(name: str, *, components: list[str] | None = None) -> dict[str, Any]:
    theme = load_theme(name)
    legacy_ok, legacy_message = _run_legacy(name)
    if not legacy_ok:
        raise RuntimeError(f"legacy theme generator failed for {name}: {legacy_message or 'no error output'}")

    semantic_ok, semantic_message = _sync_semantic_wallpaper(name)
    component_result = apply_all(theme, components)
    noctalia_ok, noctalia_message = _sync_noctalia(name)

    hypr_ok, hypr_message = _reload_hyprland()
    static_wallpaper_ok, static_wallpaper_message = _apply_static_wallpaper(name)
    starship_ok, starship_message = _sync_starship_runtime(theme)

    ACTIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.write_text(name + "\n", encoding="utf-8")
    return {
        "name": name,
        "legacy_ok": legacy_ok,
        "legacy_message": legacy_message,
        "wallpaper_ok": static_wallpaper_ok or semantic_ok,
        "wallpaper_message": static_wallpaper_message or semantic_message,
        "hyprland_ok": hypr_ok,
        "hyprland_message": hypr_message,
        "starship_ok": starship_ok,
        "starship_message": starship_message,
        "noctalia_ok": noctalia_ok,
        "noctalia_message": noctalia_message,
        "components": component_result,
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
    return apply_theme(name)
