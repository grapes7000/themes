#!/usr/bin/env python3
"""Qt/QML bridge for Theme Studio.

The UI stays deliberately thin: ThemeEditor owns draft/history/recovery/save
semantics and theme_runtime owns applying/restoring desktop state.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QImage

import theme_runtime
from theme_editor import EditorError, ThemeEditor, list_themes

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_WALLPAPER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".jxl"}

ROLE_FIELDS = (
    ("bg", "Background"),
    ("bg_alt", "Raised background"),
    ("text", "Primary text"),
    ("text_dim", "Muted text"),
    ("focus", "Focus"),
    ("border_normal", "Border"),
    ("accent", "Accent"),
    ("accent2", "Accent 2"),
    ("urgent", "Urgent"),
    ("sel_bg", "Selection background"),
    ("sel_fg", "Selection text"),
    ("cursor", "Cursor"),
)

STYLE_FIELDS = (
    ("corner_radius", "Corner radius", "int"),
    ("opacity", "Opacity", "float"),
    ("opacity_inactive", "Inactive opacity", "float"),
    ("inactive_dim", "Inactive dim", "float"),
    ("blur_on", "Blur", "boolstr"),
    ("blur_strength", "Blur strength", "int"),
    ("shadow_on", "Shadow", "boolstr"),
    ("shadow_radius", "Shadow radius", "int"),
    ("shadow_opacity", "Shadow opacity", "float"),
    ("shadow_color", "Shadow color", "color"),
    ("shadow_offset", "Shadow offset", "int"),
    ("gaps", "Gaps", "int"),
    ("border_width", "Border width", "int"),
)


class ThemeStudioBridge(QObject):
    stateChanged = Signal()
    themesChanged = Signal()
    statusChanged = Signal()
    wallpapersChanged = Signal()
    selectedWallpaperChanged = Signal()

    def __init__(self, initial_theme: str | None = None) -> None:
        super().__init__()
        self._editor: ThemeEditor | None = None
        self._status = "Theme Studio ready"
        self._live_preview = True
        self._restore_name = theme_runtime.active_theme()
        self._wallpaper_dir = Path(os.environ.get(
            "THEME_STUDIO_WALLPAPER_DIR", theme_runtime.CFG / "hypr" / "wallpapers"
        )).expanduser()
        self._wallpapers: list[dict[str, str]] = []
        self._selected_wallpaper = -1
        self._load_initial(initial_theme)
        self.refreshWallpapers()

    def _load_initial(self, initial_theme: str | None) -> None:
        names = list_themes()
        target = initial_theme or self._restore_name or (names[0] if names else None)
        if target:
            self._open_editor(target, preview=False)
        else:
            self._set_status("No themes found in ~/.config/hypr/themes")

    def _preview(self, data: dict[str, Any], reason: str) -> None:
        theme_runtime.preview_theme(data, reason)

    def _restore(self, _editor_theme_name: str) -> None:
        if self._restore_name:
            theme_runtime.restore_theme(self._restore_name)
        else:
            theme_runtime.cleanup_preview()

    def _open_editor(self, name: str, *, preview: bool) -> None:
        if self._editor and self._editor.dirty:
            self._editor.cancel()
        editor = ThemeEditor(
            name,
            preview_callback=self._preview,
            restore_callback=self._restore,
        )
        editor.desktop_preview = self._live_preview
        self._editor = editor
        self._set_status(f"Editing {name}")
        self.stateChanged.emit()
        if preview and self._live_preview:
            editor.preview(f"Open {name}")

    def _set_status(self, text: str) -> None:
        self._status = text
        self.statusChanged.emit()

    def _editor_or_none(self) -> ThemeEditor | None:
        return self._editor

    @Property(str, notify=themesChanged)
    def themesJson(self) -> str:  # noqa: N802
        return json.dumps(list_themes())

    @Property(str, notify=wallpapersChanged)
    def wallpaperDirectory(self) -> str:  # noqa: N802
        return str(self._wallpaper_dir)

    @Property(str, notify=wallpapersChanged)
    def wallpapersJson(self) -> str:  # noqa: N802
        return json.dumps(self._wallpapers)

    @Property(int, notify=selectedWallpaperChanged)
    def selectedWallpaperIndex(self) -> int:  # noqa: N802
        return self._selected_wallpaper

    @Property(str, notify=selectedWallpaperChanged)
    def selectedWallpaperUrl(self) -> str:  # noqa: N802
        if 0 <= self._selected_wallpaper < len(self._wallpapers):
            return self._wallpapers[self._selected_wallpaper]["url"]
        return ""

    @Property(str, notify=selectedWallpaperChanged)
    def selectedWallpaperName(self) -> str:  # noqa: N802
        if 0 <= self._selected_wallpaper < len(self._wallpapers):
            return self._wallpapers[self._selected_wallpaper]["name"]
        return ""

    @Property(str, notify=stateChanged)
    def themeName(self) -> str:  # noqa: N802
        return self._editor.theme_name if self._editor else ""

    @Property(str, notify=stateChanged)
    def activeTheme(self) -> str:  # noqa: N802
        return theme_runtime.active_theme() or ""

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return bool(self._editor and self._editor.dirty)

    @Property(bool, notify=stateChanged)
    def canUndo(self) -> bool:  # noqa: N802
        return bool(self._editor and self._editor.undo_stack)

    @Property(bool, notify=stateChanged)
    def canRedo(self) -> bool:  # noqa: N802
        return bool(self._editor and self._editor.redo_stack)

    @Property(bool, notify=stateChanged)
    def dark(self) -> bool:
        return bool(self._editor and self._editor.draft.get("dark", True))

    @Property(bool, notify=stateChanged)
    def livePreview(self) -> bool:  # noqa: N802
        return self._live_preview

    @Property(str, notify=statusChanged)
    def statusMessage(self) -> str:  # noqa: N802
        return self._status

    @Property(str, notify=stateChanged)
    def roleRowsJson(self) -> str:  # noqa: N802
        roles = self._editor.draft.get("roles", {}) if self._editor else {}
        rows = [{"key": key, "label": label, "value": str(roles.get(key, ""))}
                for key, label in ROLE_FIELDS]
        return json.dumps(rows)

    @Property(str, notify=stateChanged)
    def styleRowsJson(self) -> str:  # noqa: N802
        style = self._editor.draft.get("style", {}) if self._editor else {}
        rows = [{"key": key, "label": label, "type": kind,
                 "value": str(style.get(key, ""))}
                for key, label, kind in STYLE_FIELDS]
        return json.dumps(rows)

    @Property(str, notify=stateChanged)
    def validationJson(self) -> str:  # noqa: N802
        return json.dumps(self._editor.validate() if self._editor else [])

    @Property(str, notify=stateChanged)
    def validationSummary(self) -> str:  # noqa: N802
        if not self._editor:
            return "No theme loaded"
        issues = self._editor.validate()
        errors = sum(1 for issue in issues if issue.get("level") == "error")
        warnings = len(issues) - errors
        return f"{errors} error(s), {warnings} suggestion(s)"

    @Slot(str)
    def selectTheme(self, name: str) -> None:  # noqa: N802
        name = name.strip()
        if not name or name == self.themeName:
            return
        try:
            self._open_editor(name, preview=True)
        except Exception as exc:
            self._set_status(f"Could not open {name}: {exc}")

    @Slot(str, str)
    def setRole(self, key: str, value: str) -> None:  # noqa: N802
        editor = self._editor_or_none()
        value = value.strip()
        if not editor:
            return
        if not _HEX.fullmatch(value):
            self._set_status(f"{key}: use a color like #ff1493")
            return
        editor.mutate(
            f"Set {key}",
            lambda draft: draft.setdefault("roles", {}).__setitem__(key, value),
        )
        self._set_status(f"Updated {key}")
        self.stateChanged.emit()

    @Slot(str, str)
    def setStyle(self, key: str, value: str) -> None:  # noqa: N802
        editor = self._editor_or_none()
        if not editor:
            return
        kind = next((item_kind for item_key, _label, item_kind in STYLE_FIELDS
                     if item_key == key), "str")
        raw = value.strip()
        try:
            if kind == "int":
                parsed: Any = int(raw)
            elif kind == "float":
                parsed = float(raw)
            elif kind == "boolstr":
                lowered = raw.lower()
                if lowered not in {"true", "false"}:
                    raise ValueError("expected true or false")
                parsed = lowered
            elif kind == "color":
                if not _HEX.fullmatch(raw):
                    raise ValueError("expected #RRGGBB")
                parsed = raw
            else:
                parsed = raw
        except ValueError as exc:
            self._set_status(f"{key}: invalid value ({exc})")
            return
        editor.mutate(
            f"Set {key}",
            lambda draft: draft.setdefault("style", {}).__setitem__(key, parsed),
        )
        self._set_status(f"Updated {key}")
        self.stateChanged.emit()

    @Slot(bool)
    def setDark(self, enabled: bool) -> None:  # noqa: N802
        editor = self._editor_or_none()
        if not editor:
            return
        editor.mutate("Set dark mode", lambda draft: draft.__setitem__("dark", bool(enabled)))
        self._set_status("Updated light/dark metadata")
        self.stateChanged.emit()

    @Slot(bool)
    def setLivePreview(self, enabled: bool) -> None:  # noqa: N802
        self._live_preview = bool(enabled)
        if self._editor:
            self._editor.set_desktop_preview(self._live_preview)
        self._set_status("Live preview on" if enabled else "Live preview off")
        self.stateChanged.emit()

    @Slot()
    def undo(self) -> None:
        if self._editor:
            label = self._editor.undo()
            self._set_status(f"Undid {label}" if label else "Nothing to undo")
            self.stateChanged.emit()

    @Slot()
    def redo(self) -> None:
        if self._editor:
            label = self._editor.redo()
            self._set_status(f"Redid {label}" if label else "Nothing to redo")
            self.stateChanged.emit()

    @Slot()
    def previewNow(self) -> None:  # noqa: N802
        if not self._editor:
            return
        try:
            self._editor.preview("Manual preview")
            self._set_status(f"Previewing {self.themeName}")
        except Exception as exc:
            self._set_status(f"Preview failed: {exc}")

    @Slot()
    def applySaved(self) -> None:  # noqa: N802
        if not self._editor:
            return
        if self._editor.dirty:
            self._set_status("Save changes before applying the saved theme")
            return
        try:
            theme_runtime.apply_saved_theme(self.themeName)
            self._restore_name = self.themeName
            self._set_status(f"Applied {self.themeName}")
            self.stateChanged.emit()
        except Exception as exc:
            self._set_status(f"Apply failed: {exc}")

    @Slot()
    def saveAndApply(self) -> None:  # noqa: N802
        if not self._editor:
            return
        try:
            path = self._editor.save(apply=False)
            theme_runtime.apply_saved_theme(self._editor.theme_name)
            self._restore_name = self._editor.theme_name
            self._set_status(f"Saved & applied {path.name}")
            self.stateChanged.emit()
            self.themesChanged.emit()
        except EditorError as exc:
            self._set_status(str(exc))
        except Exception as exc:
            self._set_status(f"Save/apply failed: {exc}")

    @Slot()
    def cancelChanges(self) -> None:  # noqa: N802
        if not self._editor:
            return
        try:
            self._editor.cancel()
            self._set_status("Changes cancelled; desktop restored")
        except Exception as exc:
            self._set_status(f"Restore failed: {exc}")
        self.stateChanged.emit()

    @Slot()
    def reloadThemes(self) -> None:  # noqa: N802
        self.themesChanged.emit()
        self._set_status("Theme list refreshed")

    @Slot()
    def refreshWallpapers(self) -> None:  # noqa: N802
        self._wallpaper_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(
            (path for path in self._wallpaper_dir.iterdir()
             if path.is_file() and path.suffix.lower() in _WALLPAPER_EXTENSIONS),
            key=lambda path: path.name.casefold(),
        )
        previous = self.selectedWallpaperName
        self._wallpapers = [
            {"name": path.name, "path": str(path), "url": QUrl.fromLocalFile(str(path)).toString()}
            for path in files
        ]
        self._selected_wallpaper = next(
            (index for index, item in enumerate(self._wallpapers) if item["name"] == previous),
            0 if self._wallpapers else -1,
        )
        self.wallpapersChanged.emit()
        self.selectedWallpaperChanged.emit()
        self._set_status(
            f"{len(self._wallpapers)} wallpaper{'s' if len(self._wallpapers) != 1 else ''} in {self._wallpaper_dir}"
        )

    @Slot(str)
    def setWallpaperDirectory(self, directory: str) -> None:  # noqa: N802
        path = Path(directory).expanduser()
        if not path.is_dir():
            self._set_status(f"Wallpaper folder does not exist: {path}")
            return
        self._wallpaper_dir = path.resolve()
        self.refreshWallpapers()

    @Slot(int)
    def selectWallpaper(self, index: int) -> None:  # noqa: N802
        if not self._wallpapers:
            return
        self._selected_wallpaper = max(0, min(index, len(self._wallpapers) - 1))
        self.selectedWallpaperChanged.emit()

    def _selected_wallpaper_path(self) -> Path | None:
        if not (0 <= self._selected_wallpaper < len(self._wallpapers)):
            return None
        return Path(self._wallpapers[self._selected_wallpaper]["path"])

    @Slot()
    def applySelectedWallpaper(self) -> None:  # noqa: N802
        path = self._selected_wallpaper_path()
        if not path:
            self._set_status("Select a wallpaper first")
            return
        try:
            theme_runtime.apply_wallpaper_path(path)
            self._set_status(f"Applied {path.name}; it is an override until the next theme switch")
        except Exception as exc:
            self._set_status(f"Could not apply wallpaper: {exc}")

    @Slot(str)
    def bindSelectedWallpaper(self, theme: str) -> None:  # noqa: N802
        path = self._selected_wallpaper_path()
        if not path:
            self._set_status("Select a wallpaper first")
            return
        if theme not in list_themes():
            self._set_status(f"Unknown theme: {theme}")
            return
        image = QImage(str(path))
        if image.isNull():
            self._set_status(f"Could not decode {path.name}")
            return
        destination = theme_runtime.CFG / "hypr" / "wallpapers" / f"{theme}.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{theme}.", suffix=".png", dir=destination.parent)
        os.close(fd)
        temporary_path = Path(temporary)
        try:
            if not image.save(str(temporary_path), "PNG"):
                raise OSError("Qt could not encode the image as PNG")
            os.replace(temporary_path, destination)
        except Exception as exc:
            temporary_path.unlink(missing_ok=True)
            self._set_status(f"Could not bind wallpaper: {exc}")
            return
        self._set_status(f"Bound {path.name} to {theme}; it will apply when that theme is selected")

    @Slot()
    def closeSession(self) -> None:  # noqa: N802
        if not self._editor:
            return
        try:
            if self._editor.desktop_preview:
                self._restore(self._editor.theme_name)
            else:
                theme_runtime.cleanup_preview()
        except Exception:
            theme_runtime.cleanup_preview()
