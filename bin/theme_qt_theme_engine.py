#!/usr/bin/env python3
"""Expose the generated theme-engine contract to the Qt Theme Studio shell."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, QObject, Property, Signal, Slot

CONTRACT_ENV = "QT_APP_THEME_CONTRACT"
DEFAULT_CONTRACT = Path.home() / ".config" / "theme-engine" / "generated" / "theme.json"
_HEX_RE = re.compile(r"^[0-9a-fA-F]{6}$")

FALLBACK = {
    "dark": {"bg": "#141319", "bgElevated": "#1B1A22", "surface": "#211F2A", "surfaceAlt": "#262432", "surfaceHover": "#2C2A3A", "surfaceActive": "#322F44", "border": "#33303F", "borderStrong": "#46415C", "textPrimary": "#ECE9F4", "textSecondary": "#A8A3BA", "textMuted": "#6F6A80", "accent": "#8B7CF8", "accentStrong": "#A294FB", "success": "#5FD38C", "warn": "#E9C46A", "danger": "#F2768A", "info": "#7CB8F8", "focusRing": "#A294FB", "selection": "#8B7CF8", "onAccent": "#14131A"},
    "light": {"bg": "#F6F5FB", "bgElevated": "#FFFFFF", "surface": "#FFFFFF", "surfaceAlt": "#F1EFF7", "surfaceHover": "#E9E6F2", "surfaceActive": "#E0DCF0", "border": "#E2DFEE", "borderStrong": "#C8C2DE", "textPrimary": "#211F2A", "textSecondary": "#5C576E", "textMuted": "#8F8AA0", "accent": "#6C5CE7", "accentStrong": "#5748C9", "success": "#2F9E5F", "warn": "#B8860B", "danger": "#D64563", "info": "#2D7DD2", "focusRing": "#6C5CE7", "selection": "#6C5CE7", "onAccent": "#FFFFFF"},
}

ROLE_MAP = {"bg": ("bg",), "bgElevated": ("bg_alt",), "surface": ("surface_0", "overlay", "bg_alt"), "surfaceAlt": ("surface_1", "surface_0", "overlay"), "surfaceHover": ("hover", "surface_2", "surface_1"), "surfaceActive": ("focus", "hover", "surface_2"), "border": ("border_normal", "border_subtle"), "borderStrong": ("border_strong", "focus"), "textPrimary": ("text",), "textSecondary": ("text_dim", "text"), "textMuted": ("disabled", "text_dim"), "accent": ("accent", "focus"), "accentStrong": ("accent2", "accent"), "success": ("success", "ansi_green"), "warn": ("warning", "ansi_yellow"), "danger": ("urgent", "ansi_red"), "info": ("info", "ansi_blue"), "focusRing": ("focus", "accent"), "selection": ("sel_bg", "selected", "focus"), "onAccent": ("on_accent", "on_urgent")}


def _hex(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    raw = value.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    return f"#{raw.upper()}" if _HEX_RE.fullmatch(raw) else None


def _rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _blend(fg: str, bg: str, alpha: float) -> str:
    f, b = _rgb(fg), _rgb(bg)
    rgb = tuple(round(fc * alpha + bc * (1.0 - alpha)) for fc, bc in zip(f, b))
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def contract_path() -> Path:
    return Path(os.environ.get(CONTRACT_ENV, DEFAULT_CONTRACT)).expanduser()


def resolve_contract(path: Path | None = None) -> dict:
    path = path or contract_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    dark = bool(data.get("dark", True))
    roles = data.get("roles") if isinstance(data.get("roles"), dict) else {}
    style = data.get("style") if isinstance(data.get("style"), dict) else {}
    palette = dict(FALLBACK["dark" if dark else "light"])
    for token, candidates in ROLE_MAP.items():
        for role in candidates:
            value = _hex(roles.get(role))
            if value:
                palette[token] = value
                break
    bg = palette["bg"]
    palette["accentSoft"] = _blend(palette["accent"], bg, 0.14)
    palette["accentSoftHover"] = _blend(palette["accent"], bg, 0.22)
    palette["successSoft"] = _blend(palette["success"], bg, 0.14)
    palette["warnSoft"] = _blend(palette["warn"], bg, 0.14)
    palette["dangerSoft"] = _blend(palette["danger"], bg, 0.14)
    palette["infoSoft"] = _blend(palette["info"], bg, 0.14)
    palette["scrim"] = _blend("#000000", bg, 0.55)
    if not (_hex(roles.get("on_accent")) or _hex(roles.get("on_urgent"))):
        r, g, b = _rgb(palette["accent"])
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        palette["onAccent"] = "#000000" if luminance > 128 else "#FFFFFF"
    return {"name": str(data.get("name") or "Built-in"), "dark": dark, "fontFamily": str(style.get("font_family") or ""), "colors": palette, "source": str(path), "connected": bool(data)}


class ThemeBridge(QObject):
    themeChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._path = contract_path()
        self._watcher = QFileSystemWatcher(self)
        self._state = resolve_contract(self._path)
        self._watcher.fileChanged.connect(self._on_change)
        self._watcher.directoryChanged.connect(self._on_change)
        self._rewatch()

    def _rewatch(self) -> None:
        watched = self._watcher.files() + self._watcher.directories()
        if watched:
            self._watcher.removePaths(watched)
        if self._path.parent.exists():
            self._watcher.addPath(str(self._path.parent))
        if self._path.exists():
            self._watcher.addPath(str(self._path))

    @Slot()
    def reload(self) -> None:
        self._state = resolve_contract(self._path)
        self._rewatch()
        self.themeChanged.emit()

    @Slot(str)
    def _on_change(self, _path: str = "") -> None:
        self.reload()

    @Property(str, notify=themeChanged)
    def name(self) -> str:
        return self._state["name"]

    @Property(bool, notify=themeChanged)
    def dark(self) -> bool:
        return self._state["dark"]

    @Property(str, notify=themeChanged)
    def fontFamily(self) -> str:  # noqa: N802
        return self._state["fontFamily"]

    @Property(str, notify=themeChanged)
    def colorsJson(self) -> str:  # noqa: N802
        return json.dumps(self._state["colors"])

    @Property(str, notify=themeChanged)
    def sourcePath(self) -> str:  # noqa: N802
        return self._state["source"]

    @Property(bool, notify=themeChanged)
    def connected(self) -> bool:
        return self._state["connected"]
