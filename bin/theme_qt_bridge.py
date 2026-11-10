"""Qt/QML bridge for Theme Studio.

The UI stays deliberately thin: ThemeEditor owns draft/history/recovery/save
semantics and theme_runtime owns applying/restoring desktop state.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import theme_runtime
import theme_ui
from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QImage
from theme_editor import EditorError, ThemeEditor, list_themes
from theme_schema import (
    ALL_ROLES,
    COMPONENT_FIELDS,
    ROLE_LABELS,
    WINDOW_PRESETS,
    FieldSpec,
    apply_window_preset,
    contrast_ratio,
    deep_get,
    deep_set,
    ensure_theme_schema,
    generate_palette_from_seed,
    is_hex,
    palette_from_wallpaper,
    safe_theme_name,
)

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_SHELL_MOTION = {
    "motion_fast_ms": ("Fast transitions", 0, 500, 90, 140),
    "motion_normal_ms": ("Normal transitions", 0, 800, 120, 180),
    "motion_hover_percent": ("Hover size", 100, 130, 103, 110),
    "motion_press_percent": ("Pressed size", 80, 100, 99, 97),
    "motion_overshoot_percent": ("Release bounce", 0, 300, 0, 145),
}
_WALLPAPER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".jxl"}
_SEMANTIC_ROLES = (
    "bg",
    "bg_alt",
    "text",
    "text_dim",
    "accent",
    "accent2",
    "focus",
    "success",
    "warning",
    "info",
    "urgent",
    "ansi_black",
    "ansi_red",
    "ansi_green",
    "ansi_yellow",
    "ansi_blue",
    "ansi_magenta",
    "ansi_cyan",
    "ansi_white",
    "ansi_br_black",
    "ansi_br_red",
    "ansi_br_green",
    "ansi_br_yellow",
    "ansi_br_blue",
    "ansi_br_magenta",
    "ansi_br_cyan",
    "ansi_br_white",
)

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

STYLE_COMPONENT_PATHS = {
    "corner_radius": "corner_radius",
    "opacity": "active_opacity",
    "opacity_inactive": "inactive_opacity",
    "inactive_dim": "inactive_dim",
    "blur_on": "blur.enabled",
    "blur_strength": "blur.size",
    "shadow_on": "shadow.enabled",
    "shadow_radius": "shadow.radius",
    "shadow_opacity": "shadow.opacity",
    "shadow_color": "shadow.color",
    "shadow_offset": "shadow.offset",
    "gaps": "gaps_out",
    "border_width": "border_width",
}

QUICKSHELL_FIELDS = (
    FieldSpec(
        "components.homepage.bar_position",
        "Bar position",
        "choice",
        choices=("top", "bottom"),
    ),
    FieldSpec("components.homepage.bar_surface_role", "Bar surface", "role"),
    FieldSpec("components.homepage.bar_opacity", "Bar opacity", "float", 0, 1, 0.01),
    FieldSpec("components.homepage.bar_outline_role", "Bar outline", "role"),
    FieldSpec(
        "components.homepage.bar_outline_opacity",
        "Bar outline opacity",
        "float",
        0,
        1,
        0.01,
    ),
    FieldSpec("components.homepage.drawer_width", "Drawer width", "int", 260, 1000, 10),
    FieldSpec("components.homepage.drawer_surface_role", "Drawer surface", "role"),
    FieldSpec(
        "components.homepage.drawer_opacity", "Drawer opacity", "float", 0, 1, 0.01
    ),
    FieldSpec("components.homepage.drawer_outline_role", "Drawer outline", "role"),
    FieldSpec(
        "components.homepage.drawer_outline_opacity",
        "Drawer outline opacity",
        "float",
        0,
        1,
        0.01,
    ),
    FieldSpec(
        "components.homepage.card_opacity", "Homepage card opacity", "float", 0, 1, 0.01
    ),
    FieldSpec(
        "components.homepage.image_fit",
        "Wallpaper fit",
        "choice",
        choices=("cover", "contain", "fill", "fit"),
    ),
    FieldSpec(
        "components.homepage.slideshow_seconds", "Slideshow seconds", "int", 5, 600, 5
    ),
    FieldSpec(
        "components.homepage.image_overlay_opacity",
        "Wallpaper overlay",
        "float",
        0,
        0.5,
        0.01,
    ),
    FieldSpec(
        "components.homepage.image_dimming", "Wallpaper dimming", "float", 0, 0.85, 0.01
    ),
    FieldSpec(
        "components.homepage.transition_ms",
        "Homepage transition (ms)",
        "int",
        0,
        2000,
        10,
    ),
)

QUICKSHELL_DEFAULTS = {
    "bar_position": "top",
    "bar_surface_role": "surface_0",
    "bar_opacity": 0.96,
    "bar_outline_role": "border_subtle",
    "bar_outline_opacity": 0.72,
    "drawer_width": 420,
    "drawer_surface_role": "surface_1",
    "drawer_opacity": 0.97,
    "drawer_outline_role": "border_subtle",
    "drawer_outline_opacity": 0.76,
    "card_opacity": 0.92,
    "image_fit": "cover",
    "slideshow_seconds": 30,
    "image_overlay_opacity": 0.10,
    "image_dimming": 0.28,
    "transition_ms": 320,
}


class ThemeStudioBridge(QObject):
    stateChanged = Signal()
    themesChanged = Signal()
    statusChanged = Signal()
    wallpapersChanged = Signal()
    selectedWallpaperChanged = Signal()
    recolorChanged = Signal()
    eyedropperChanged = Signal()

    def __init__(self, initial_theme: str | None = None) -> None:
        super().__init__()
        self._editor: ThemeEditor | None = None
        self._status = "Theme Studio ready"
        self._live_preview = True
        self._preview_active = False
        self._preview_error = False
        self._ui_override_snapshot = theme_ui.override_name()
        self._ui_override_modified = False
        self._restore_name = theme_runtime.active_theme()
        # Shape/texture profiles live outside individual theme JSON files.  A
        # manual Windows edit temporarily disables the relevant profile so the
        # requested value can actually reach Hyprland; retain the exact prior
        # profile so Cancel remains a true cancel.
        self._effects_snapshot = self._read_effects_profile()
        self._effects_modified = False
        self._wallpaper_dir = Path(
            os.environ.get(
                "THEME_STUDIO_WALLPAPER_DIR", theme_runtime.CFG / "hypr" / "wallpapers"
            )
        ).expanduser()
        self._wallpapers: list[dict[str, str]] = []
        self._selected_wallpaper = -1
        self._template_name = ""
        self._regions: list[dict[str, str]] = []
        self._recolor_preview_url = ""
        self._recolor_preview_theme = ""
        self._eyedropper_image: QImage | None = None
        self._eyedropper_path = ""
        self._load_initial(initial_theme)
        self.refreshWallpapers()

    @staticmethod
    def _read_effects_profile() -> dict[str, Any] | None:
        try:
            import theme_effects

            path = Path(theme_effects.PROFILE_PATH)
            if not path.is_file():
                return None
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else None
        except (ImportError, OSError, ValueError):
            return None

    def _clear_effect_override(self, axis: str) -> None:
        try:
            import theme_effects

            active = {
                "shape": theme_effects.profile_shape,
                "texture": theme_effects.profile_texture,
                "anim": theme_effects.profile_anim,
            }[axis]()
            if not active:
                return
            if axis == "shape":
                theme_effects.save_shape(None)
            elif axis == "anim":
                theme_effects.save_anim(None)
            else:
                theme_effects.save_texture(None)
            self._effects_modified = True
        except (ImportError, OSError, ValueError):
            pass

    def _restore_effect_overrides(self) -> bool:
        if not self._effects_modified:
            return False
        try:
            import theme_effects

            profile_path = Path(theme_effects.PROFILE_PATH)
            if self._effects_snapshot is None:
                profile_path.unlink(missing_ok=True)
            else:
                theme_effects._save_profile_raw(dict(self._effects_snapshot))
        except (ImportError, OSError, ValueError):
            return False
        self._effects_modified = False
        return True

    def _load_initial(self, initial_theme: str | None) -> None:
        names = list_themes()
        target = initial_theme or self._restore_name or (names[0] if names else None)
        if target:
            self._open_editor(target, preview=False)
        else:
            self._set_status("No themes found in ~/.config/hypr/themes")

    def _preview(self, data: dict[str, Any], reason: str) -> None:
        try:
            self._preview_active = True
            theme_runtime.preview_theme(data, reason)
            self._preview_error = False
            self._set_status(f"Live preview: {reason}")
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as exc:
            self._preview_error = True
            # Keep the draft/undo stack intact and make the problem visible in
            # the app instead of letting a Qt slot fail silently.
            self._set_status(f"Live preview failed: {exc}")

    def _restore(self, _editor_theme_name: str) -> None:
        if self._restore_name:
            theme_runtime.restore_theme(self._restore_name)
        else:
            theme_runtime.cleanup_preview()
        self._preview_active = False

    def _open_editor(self, name: str, *, preview: bool) -> None:
        self._restore_ui_override()
        if self._editor and self._editor.dirty:
            self._editor.cancel()
            if self._restore_effect_overrides() and self._restore_name:
                theme_runtime.apply_saved_theme(self._restore_name)
        if self._editor and self._preview_active:
            self._restore(self._editor.theme_name)
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

    def _restore_ui_override(self) -> None:
        if self._ui_override_modified:
            theme_ui.set_override(self._ui_override_snapshot)
            self._ui_override_modified = False

    def _set_status(self, text: str) -> None:
        self._status = text
        self.statusChanged.emit()

    def _editor_or_none(self) -> ThemeEditor | None:
        return self._editor

    @Property(str, notify=themesChanged)
    def themesJson(self) -> str:
        return json.dumps(list_themes())

    @Property(str, notify=wallpapersChanged)
    def wallpaperDirectory(self) -> str:
        return str(self._wallpaper_dir)

    @Property(str, notify=wallpapersChanged)
    def wallpapersJson(self) -> str:
        return json.dumps(self._wallpapers)

    @Property(int, notify=selectedWallpaperChanged)
    def selectedWallpaperIndex(self) -> int:
        return self._selected_wallpaper

    @Property(str, notify=selectedWallpaperChanged)
    def selectedWallpaperUrl(self) -> str:
        if 0 <= self._selected_wallpaper < len(self._wallpapers):
            return self._wallpapers[self._selected_wallpaper]["url"]
        return ""

    @Property(str, notify=selectedWallpaperChanged)
    def selectedWallpaperName(self) -> str:
        if 0 <= self._selected_wallpaper < len(self._wallpapers):
            return self._wallpapers[self._selected_wallpaper]["name"]
        return ""

    @Property(str, notify=recolorChanged)
    def recolorTemplateName(self) -> str:
        return self._template_name

    @Property(str, notify=recolorChanged)
    def recolorRegionsJson(self) -> str:
        return json.dumps(self._regions)

    @Property(str, notify=recolorChanged)
    def recolorPreviewUrl(self) -> str:
        return self._recolor_preview_url

    @Property(str, constant=True)
    def semanticRolesJson(self) -> str:
        return json.dumps(_SEMANTIC_ROLES)

    @Property(str, notify=eyedropperChanged)
    def eyedropperImageUrl(self) -> str:
        return (
            QUrl.fromLocalFile(self._eyedropper_path).toString()
            if self._eyedropper_path
            else ""
        )

    @Property(str, notify=stateChanged)
    def themeName(self) -> str:
        return self._current_theme_name()

    def _current_theme_name(self) -> str:
        return self._editor.theme_name if self._editor else ""

    @Property(str, notify=stateChanged)
    def activeTheme(self) -> str:
        return theme_runtime.active_theme() or ""

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return bool((self._editor and self._editor.dirty) or self._ui_override_modified)

    @Property(bool, notify=stateChanged)
    def canUndo(self) -> bool:
        return bool(self._editor and self._editor.undo_stack)

    @Property(bool, notify=stateChanged)
    def canRedo(self) -> bool:
        return bool(self._editor and self._editor.redo_stack)

    @Property(bool, notify=stateChanged)
    def dark(self) -> bool:
        return self._current_dark()

    def _current_dark(self) -> bool:
        return bool(self._editor and self._editor.draft.get("dark", True))

    @Property(bool, notify=stateChanged)
    def livePreview(self) -> bool:
        return self._live_preview

    @Property(str, notify=statusChanged)
    def statusMessage(self) -> str:
        return self._status

    @Property(str, notify=stateChanged)
    def roleRowsJson(self) -> str:
        roles = self._editor.draft.get("roles", {}) if self._editor else {}
        rows = [
            {"key": key, "label": label, "value": str(roles.get(key, ""))}
            for key, label in ROLE_FIELDS
        ]
        return json.dumps(rows)

    @Property(str, notify=stateChanged)
    def paletteRowsJson(self) -> str:
        """Every semantic role, with a readable label and contrast health."""
        roles = self._editor.draft.get("roles", {}) if self._editor else {}
        background = str(roles.get("bg", "#000000"))
        rows = []
        for key in (*ALL_ROLES, *(role for role in _SEMANTIC_ROLES if role.startswith("ansi_"))):
            value = str(roles.get(key, ""))
            try:
                contrast = (
                    round(contrast_ratio(value, background), 2)
                    if is_hex(value) and is_hex(background)
                    else 0
                )
            except (TypeError, ValueError):
                contrast = 0
            rows.append(
                {
                    "key": key,
                    "label": ROLE_LABELS.get(
                        key,
                        key.replace("ansi_br_", "Terminal bright ")
                        .replace("ansi_", "Terminal ")
                        .replace("_", " "),
                    ),
                    "value": value,
                    "contrast": contrast,
                }
            )
        return json.dumps(rows)

    @Property(str, notify=stateChanged)
    def terminalSettingsJson(self) -> str:
        if not self._editor:
            return "{}"
        return json.dumps(self._editor.draft.get("components", {}).get("terminal", {}))

    @Property(str, notify=stateChanged)
    def styleRowsJson(self) -> str:
        style = self._editor.draft.get("style", {}) if self._editor else {}
        rows = [
            {
                "key": key,
                "label": label,
                "type": kind,
                "minimum": -60
                if key == "shadow_offset"
                else (0.2 if key in {"opacity", "opacity_inactive"} else 0),
                "maximum": 1
                if kind == "float"
                else (10 if key == "border_width" else 60),
                "step": 0.01 if kind == "float" else 1,
                "value": str(style.get(key, "0")).split()[-1],
            }
            for key, label, kind in STYLE_FIELDS
        ]
        return json.dumps(rows)

    @Property(str, notify=stateChanged)
    def windowRowsJson(self) -> str:
        draft = self._editor.draft if self._editor else {}
        rows = []
        for field in COMPONENT_FIELDS.get("windows", ()):
            rows.append(
                {
                    "path": field.path,
                    "label": field.label,
                    "kind": field.kind,
                    "value": str(deep_get(draft, field.path, "")),
                    "choices": list(field.choices),
                    "advanced": bool(field.advanced),
                    "minimum": field.minimum,
                    "maximum": field.maximum,
                    "step": field.step,
                }
            )
        return json.dumps(rows)

    @Property(str, notify=stateChanged)
    def windowPresetsJson(self) -> str:
        return json.dumps(list(WINDOW_PRESETS))

    @Property(str, notify=stateChanged)
    def quickshellRowsJson(self) -> str:
        draft = self._editor.draft if self._editor else {}
        return json.dumps(
            [
                {
                    "path": field.path,
                    "label": field.label,
                    "kind": field.kind,
                    "choices": list(field.choices),
                    "minimum": field.minimum,
                    "maximum": field.maximum,
                    "step": field.step,
                    "value": str(
                        deep_get(
                            draft,
                            field.path,
                            QUICKSHELL_DEFAULTS[field.path.rsplit(".", 1)[-1]],
                        )
                    ),
                }
                for field in QUICKSHELL_FIELDS
            ]
        )

    @Property(str, notify=stateChanged)
    def quickshellMotionJson(self) -> str:
        draft = self._editor.draft if self._editor else {}
        try:
            profile = theme_ui.load_profile(theme_ui.resolved_name(draft)[0])
            overrides = draft.get("ui_style_overrides", {})
            metrics = overrides.get("metrics", {})
            motion = overrides.get("patterns", {}).get(
                "motion", profile["patterns"].get("motion", "restrained")
            )
            return json.dumps(
                [
                    {
                        "key": key,
                        "label": label,
                        "minimum": minimum,
                        "maximum": maximum,
                        "value": metrics.get(
                            key, playful if motion == "playful" else restrained
                        ),
                    }
                    for key, (
                        label,
                        minimum,
                        maximum,
                        restrained,
                        playful,
                    ) in _SHELL_MOTION.items()
                ]
            )
        except (OSError, ValueError, TypeError):
            return "[]"

    @Property(str, notify=stateChanged)
    def uiStyleJson(self) -> str:
        draft = self._editor.draft if self._editor else {}
        name, source = theme_ui.resolved_name(draft)
        try:
            profile = theme_ui.load_profile(name)
            available = theme_ui.list_profiles()
            overrides = draft.get("ui_style_overrides", {})
            metrics = {**profile["metrics"], **overrides.get("metrics", {})}
            patterns = {**profile["patterns"], **overrides.get("patterns", {})}
            rows = []
            for key, value in metrics.items():
                if key in _SHELL_MOTION:
                    continue
                maximum = 600 if "width" in key and key == "sidebar_width" else 120
                if "radius" in key:
                    maximum = 60
                elif "font" in key:
                    maximum = 48
                elif key in {"border_width", "focus_width"}:
                    maximum = 10
                rows.append(
                    {
                        "key": key,
                        "label": key.replace("_", " ").title(),
                        "kind": "metric",
                        "value": value,
                        "maximum": maximum,
                    }
                )
            for key, value in patterns.items():
                choices = sorted(
                    {
                        str(p["patterns"].get(key, value))
                        for p in (theme_ui.load_profile(item) for item in available)
                    }
                )
                rows.append(
                    {
                        "key": key,
                        "label": key.replace("_", " ").title(),
                        "kind": "pattern",
                        "value": value,
                        "choices": choices,
                    }
                )
            return json.dumps(
                {"name": name, "source": source, "profiles": available, "rows": rows}
            )
        except (OSError, ValueError, TypeError):
            return json.dumps(
                {"name": "", "source": "unavailable", "profiles": [], "rows": []}
            )

    @Slot(str)
    def selectUiStyle(self, name: str) -> None:
        if not self._editor:
            return
        try:
            theme_ui.load_profile(name)
        except (OSError, ValueError, TypeError) as exc:
            self._set_status(str(exc))
            return
        had_override = bool(theme_ui.override_name())
        unchanged = (
            self._editor.draft.get("ui_style") == name
            and "ui_style_overrides" not in self._editor.draft
        )
        if had_override:
            theme_ui.set_override(None)
            self._ui_override_modified = True

        def change(draft: dict[str, Any]) -> None:
            draft["ui_style"] = name
            draft.pop("ui_style_overrides", None)

        self._editor.mutate(f"Select UI style {name}", change)
        if had_override and unchanged and self._editor.desktop_preview:
            self._editor.preview(f"Select UI style {name}")
        self.stateChanged.emit()

    @Slot()
    def followThemeUiStyle(self) -> None:
        if not self._editor or not theme_ui.override_name():
            return
        theme_ui.set_override(None)
        self._ui_override_modified = True
        if self._editor.desktop_preview:
            self._editor.preview("Follow theme UI style")
        self._set_status("Following the theme's UI style; save to keep this choice")
        self.stateChanged.emit()

    @Slot(str, str, str)
    def setUiStyleValue(self, section: str, key: str, value: str) -> None:
        if not self._editor or section not in {"metrics", "patterns"}:
            return
        name, _ = theme_ui.resolved_name(self._editor.draft)
        try:
            profile = theme_ui.load_profile(name)
            if key not in profile[section] and not (
                section == "metrics" and key in _SHELL_MOTION
            ):
                return
            parsed: Any = int(value) if section == "metrics" else value
            if (
                section == "metrics"
                and key not in _SHELL_MOTION
                and not 0 <= parsed <= 600
            ):
                raise ValueError("UI style metric is out of range")
            if (
                key in _SHELL_MOTION
                and not _SHELL_MOTION[key][1] <= parsed <= _SHELL_MOTION[key][2]
            ):
                raise ValueError("Shell motion value is out of range")
        except (OSError, ValueError, TypeError) as exc:
            self._set_status(str(exc))
            return
        self._editor.mutate(
            f"Set UI style {key}",
            lambda draft: deep_set(
                draft, f"ui_style_overrides.{section}.{key}", parsed
            ),
        )
        self.stateChanged.emit()

    @Property(str, constant=True)
    def roleNamesJson(self) -> str:
        return json.dumps(list(ALL_ROLES))

    @Property(str, notify=stateChanged)
    def validationJson(self) -> str:
        return json.dumps(self._editor.validate() if self._editor else [])

    @Property(str, notify=stateChanged)
    def validationSummary(self) -> str:
        if not self._editor:
            return "No theme loaded"
        issues = self._editor.validate()
        errors = sum(1 for issue in issues if issue.get("level") == "error")
        warnings = len(issues) - errors
        return f"{errors} error(s), {warnings} suggestion(s)"

    @Slot(str)
    def selectTheme(self, name: str) -> None:
        name = name.strip()
        if not name or name == self._current_theme_name():
            return
        try:
            self._open_editor(name, preview=True)
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as exc:
            self._set_status(f"Could not open {name}: {exc}")

    @Slot(str, str)
    def setRole(self, key: str, value: str) -> None:
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

    def _replace_palette(
        self, label: str, roles: dict[str, str], *, dark: bool | None = None
    ) -> None:
        editor = self._editor_or_none()
        if not editor:
            return
        clean = {
            key: value.upper()
            for key, value in roles.items()
            if key in ALL_ROLES and is_hex(value)
        }
        if not clean:
            self._set_status("Palette contains no valid #RRGGBB colors")
            return

        def mutate(draft: dict[str, Any]) -> None:
            draft.setdefault("roles", {}).update(clean)
            if dark is not None:
                draft["dark"] = bool(dark)

        editor.mutate(label, mutate)
        self._set_status(label)
        self.stateChanged.emit()

    @Slot(str, bool)
    def generatePalette(self, seed: str, dark: bool) -> None:
        seed = seed.strip()
        if not is_hex(seed):
            self._set_status("Seed color must be #RRGGBB")
            return
        self._replace_palette(
            "Generated palette from seed",
            generate_palette_from_seed(seed, dark),
            dark=dark,
        )

    @Slot()
    def generatePaletteFromSelectedWallpaper(self) -> None:
        path = self._selected_wallpaper_path()
        if not path:
            self._set_status("Select a wallpaper first")
            return
        try:
            self._replace_palette(
                f"Generated palette from {path.name}",
                palette_from_wallpaper(path, self._current_dark()),
                dark=self._current_dark(),
            )
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as exc:
            self._set_status(f"Could not generate palette from wallpaper: {exc}")

    @Slot(str)
    def importPalette(self, filename: str) -> None:
        path = Path(QUrl(filename).toLocalFile() or filename).expanduser()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            roles = payload.get("roles", payload) if isinstance(payload, dict) else {}
            if not isinstance(roles, dict):
                raise TypeError(
                    "expected a palette object or a theme with a roles object"
                )
            self._replace_palette(f"Imported palette from {path.name}", roles)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self._set_status(f"Could not import palette: {exc}")

    @Slot(str)
    def exportPalette(self, filename: str) -> None:
        path = Path(QUrl(filename).toLocalFile() or filename).expanduser()
        if not path.name:
            self._set_status("Choose a file name for the exported palette")
            return
        try:
            roles = self._editor.draft.get("roles", {}) if self._editor else {}
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(
                prefix=".palette-", suffix=".json", dir=path.parent
            )
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "name": self._current_theme_name(),
                        "dark": self._current_dark(),
                        "roles": roles,
                    },
                    handle,
                    indent=2,
                )
                handle.write("\n")
            os.replace(temporary, path)
            self._set_status(f"Exported palette to {path}")
        except OSError as exc:
            self._set_status(f"Could not export palette: {exc}")

    @Slot(str)
    def duplicateTheme(self, name: str) -> None:
        editor = self._editor_or_none()
        if not editor or not name.strip():
            self._set_status("Enter a name for the new theme")
            return
        try:
            target = safe_theme_name(name)
            if editor.theme_path(target).exists():
                self._set_status(f"Theme already exists: {target}. Choose a different name.")
                return
            path = editor.save(target, apply=False)
            self._restore_name = target
            theme_runtime.apply_saved_theme(target)
            self._set_status(f"Created and applied {path.stem}")
            self.stateChanged.emit()
            self.themesChanged.emit()
        except (EditorError, OSError, ValueError) as exc:
            self._set_status(f"Could not create theme: {exc}")

    @Slot(str, str, bool)
    def createTheme(self, name: str, seed: str, dark: bool) -> None:
        if not name.strip():
            self._set_status("Enter a name for the new theme")
            return
        try:
            target = safe_theme_name(name)
        except ValueError as exc:
            self._set_status(str(exc))
            return
        if self.dirty:
            self._set_status("Save or cancel your current changes before creating a new theme")
            return
        if not is_hex(seed.strip()):
            self._set_status("Seed color must be #RRGGBB")
            return
        if target in list_themes():
            self._set_status(f"Theme already exists: {target}")
            return
        base_style = dict(self._editor.draft.get("style", {})) if self._editor else {}
        data = ensure_theme_schema(
            {
                "name": target,
                "dark": dark,
                "roles": generate_palette_from_seed(seed, dark),
                "style": base_style,
            }
        )
        self._editor = ThemeEditor.from_data(
            target, data, preview_callback=self._preview, restore_callback=self._restore
        )
        self._editor.desktop_preview = self._live_preview
        try:
            path = self._editor.save(apply=False)
            self._restore_name = target
            theme_runtime.apply_saved_theme(target)
            self._set_status(f"Created and applied {path.stem}")
            self.stateChanged.emit()
            self.themesChanged.emit()
        except (EditorError, OSError, ValueError) as exc:
            self._set_status(f"Could not create theme: {exc}")

    @Slot(result=str)
    def captureScreenForEyedropper(self) -> str:
        """Capture the primary display for the QML pixel-sampling overlay."""
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self._set_status("No screen is available for the eyedropper")
            return ""
        if QGuiApplication.platformName().startswith("wayland"):
            try:
                capture = subprocess.run(
                    ["grim", "-o", screen.name(), "-"],
                    capture_output=True,
                    check=True,
                    timeout=5,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                self._set_status(f"Could not capture the screen with grim: {exc}")
                return ""
            image = QImage.fromData(capture.stdout)
        else:
            image = screen.grabWindow(0).toImage()
        if image.isNull():
            self._set_status("Could not capture the screen for the eyedropper")
            return ""
        fd, temporary = tempfile.mkstemp(prefix="theme-eyedropper-", suffix=".png")
        os.close(fd)
        try:
            if not image.save(temporary):
                raise OSError("Qt could not encode the screen capture")
            previous = self._eyedropper_path
            self._eyedropper_path = temporary
            self._eyedropper_image = image
            if previous:
                Path(previous).unlink(missing_ok=True)
            self.eyedropperChanged.emit()
            return QUrl.fromLocalFile(self._eyedropper_path).toString()
        except OSError as exc:
            Path(temporary).unlink(missing_ok=True)
            self._set_status(f"Could not prepare eyedropper: {exc}")
            return ""

    @Slot(float, float, float, float, result=str)
    def screenColorAt(
        self, x: float, y: float, view_width: float, view_height: float
    ) -> str:
        image = self._eyedropper_image
        if image is None or image.isNull() or view_width <= 0 or view_height <= 0:
            return ""
        pixel_x = max(0, min(image.width() - 1, round(x * image.width() / view_width)))
        pixel_y = max(
            0, min(image.height() - 1, round(y * image.height() / view_height))
        )
        return image.pixelColor(pixel_x, pixel_y).name().upper()

    @Slot(str, str)
    def setStyle(self, key: str, value: str) -> None:
        editor = self._editor_or_none()
        if not editor:
            return
        kind = next(
            (
                item_kind
                for item_key, _label, item_kind in STYLE_FIELDS
                if item_key == key
            ),
            "str",
        )
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
                parsed = lowered == "true"
            elif kind == "color":
                if not _HEX.fullmatch(raw):
                    raise ValueError("expected #RRGGBB")
                parsed = raw
            else:
                parsed = raw
        except ValueError as exc:
            self._set_status(f"{key}: invalid value ({exc})")
            return
        path = STYLE_COMPONENT_PATHS.get(key)
        if path is None:
            return
        self._clear_effect_override(
            "shape" if key in {"corner_radius", "gaps", "border_width"} else "texture"
        )
        if key == "shadow_offset":
            parsed = f"0 {parsed}"
        editor.mutate(
            f"Set {key}",
            lambda draft: deep_set(draft, f"components.windows.{path}", parsed),
        )
        self._set_status(f"Updated {key}")
        self.stateChanged.emit()

    def _set_component_value(
        self, path: str, value: str, fields: tuple[Any, ...]
    ) -> None:
        editor = self._editor_or_none()
        field = next((item for item in fields if item.path == path), None)
        if not editor or not field:
            return
        raw = value.strip()
        try:
            if field.kind == "int":
                parsed: Any = int(raw)
            elif field.kind == "float":
                parsed = float(raw)
            elif field.kind == "bool":
                lowered = raw.lower()
                if lowered not in {"true", "false"}:
                    raise ValueError("expected true or false")
                parsed = lowered == "true"
            elif field.kind == "choice":
                if raw not in field.choices:
                    raise ValueError("choose " + ", ".join(field.choices))
                parsed = raw
            elif field.kind == "role":
                if raw not in ALL_ROLES and not is_hex(raw):
                    raise ValueError("choose a semantic role or #RRGGBB")
                parsed = raw
            else:
                parsed = raw
            if field.minimum is not None and parsed < field.minimum:
                raise ValueError(f"minimum is {field.minimum}")
            if field.maximum is not None and parsed > field.maximum:
                raise ValueError(f"maximum is {field.maximum}")
        except (TypeError, ValueError) as exc:
            self._set_status(f"{field.label}: invalid value ({exc})")
            return
        editor.mutate(f"Set {field.label}", lambda draft: deep_set(draft, path, parsed))
        if not (editor.desktop_preview and self._preview_error):
            self._set_status(f"Updated {field.label}")
        self.stateChanged.emit()

    @Slot(str, str)
    def setWindowValue(self, path: str, value: str) -> None:
        # Effects profiles are global, post-theme overrides.  Leaving one
        # enabled while editing the same axis makes a committed value appear
        # inert (for example, uniform-8 forces every radius back to 8).
        # Manual editor input takes precedence for the axis it owns.
        if path.startswith(
            (
                "style.animation_",
                "style.spring_",
                "style.custom_bezier_",
                "style.workspace_style",
                "style.layer_",
            )
        ):
            self._clear_effect_override("anim")
        elif path in {
            "components.windows.corner_radius",
            "components.windows.rounding_power",
            "components.windows.border_width",
            "components.windows.gaps_in",
            "components.windows.gaps_out",
        }:
            self._clear_effect_override("shape")
        elif path.startswith(
            (
                "components.windows.blur.",
                "components.windows.shadow.",
                "components.windows.active_opacity",
                "components.windows.inactive_opacity",
                "components.windows.inactive_dim",
            )
        ):
            self._clear_effect_override("texture")
        self._set_component_value(
            path, value, tuple(COMPONENT_FIELDS.get("windows", ()))
        )

    @Slot(str, int)
    def adjustWindowValue(self, path: str, direction: int) -> None:
        """GUI equivalent of the TUI editor's left/right field adjustment."""
        editor = self._editor_or_none()
        field = next(
            (item for item in COMPONENT_FIELDS.get("windows", ()) if item.path == path),
            None,
        )
        if not editor or not field or not direction:
            return
        value = deep_get(editor.draft, path)
        if field.kind == "bool":
            new_value: Any = not bool(value)
        elif field.kind in {"int", "float"}:
            new_value = float(value) + field.step * (1 if direction > 0 else -1)
            if field.minimum is not None:
                new_value = max(field.minimum, new_value)
            if field.maximum is not None:
                new_value = min(field.maximum, new_value)
            new_value = round(new_value) if field.kind == "int" else round(new_value, 4)
        elif field.kind == "choice":
            choices = list(field.choices)
            new_value = (
                choices[
                    (choices.index(value) + (1 if direction > 0 else -1)) % len(choices)
                ]
                if value in choices
                else choices[0]
            )
        elif field.kind == "role":
            choices = list(ALL_ROLES)
            new_value = (
                choices[
                    (choices.index(value) + (1 if direction > 0 else -1)) % len(choices)
                ]
                if value in choices
                else choices[0]
            )
        else:
            return
        self.setWindowValue(
            path,
            str(new_value).lower() if isinstance(new_value, bool) else str(new_value),
        )

    @Slot()
    def resetWindows(self) -> None:
        editor = self._editor_or_none()
        if not editor:
            return
        editor.reset_section("components.windows")
        self._set_status("Reset Windows")
        self.stateChanged.emit()

    @Slot(str)
    def setWindowPreset(self, name: str) -> None:
        editor = self._editor_or_none()
        if not editor or name not in WINDOW_PRESETS:
            return
        self._clear_effect_override("shape")
        self._clear_effect_override("texture")
        editor.mutate(
            f"Apply {name.replace('_', ' ')} window preset",
            lambda draft: apply_window_preset(draft, name),
        )
        self._set_status(f"Applied {name.replace('_', ' ')} window preset")
        self.stateChanged.emit()

    @Slot(str)
    def setMotionProfile(self, name: str) -> None:
        from theme_motion import EFFECT_PROFILES
        from theme_schema import apply_mapping

        editor = self._editor_or_none()
        if not editor or name not in EFFECT_PROFILES:
            return
        self._clear_effect_override("texture")
        self._clear_effect_override("anim")
        editor.mutate(
            f"Apply {name} motion profile",
            lambda draft: apply_mapping(draft, EFFECT_PROFILES[name]),
        )
        self._set_status(f"Applied {name} motion profile")
        self.stateChanged.emit()

    @Slot(str, str)
    def setQuickshellValue(self, path: str, value: str) -> None:
        self._set_component_value(path, value, QUICKSHELL_FIELDS)

    @Slot(bool)
    def setDark(self, enabled: bool) -> None:
        editor = self._editor_or_none()
        if not editor:
            return
        editor.mutate(
            "Set dark mode", lambda draft: draft.__setitem__("dark", bool(enabled))
        )
        self._set_status("Updated light/dark metadata")
        self.stateChanged.emit()

    @Slot(bool)
    def setLivePreview(self, enabled: bool) -> None:
        self._live_preview = bool(enabled)
        if self._editor:
            self._editor.set_desktop_preview(self._live_preview)
        if not (enabled and self._preview_error):
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
    def previewNow(self) -> None:
        if not self._editor:
            return
        try:
            self._editor.preview("Manual preview")
            if not self._preview_error:
                self._set_status(f"Previewing {self._current_theme_name()}")
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as exc:
            self._set_status(f"Preview failed: {exc}")

    @Slot()
    def applySaved(self) -> None:
        if not self._editor:
            return
        if self._editor.dirty:
            self._set_status("Save changes before applying the saved theme")
            return
        try:
            theme_runtime.apply_saved_theme(self._editor.theme_name)
            self._preview_active = False
            self._restore_name = self._editor.theme_name
            self._ui_override_snapshot = theme_ui.override_name()
            self._ui_override_modified = False
            self._set_status(f"Applied {self._editor.theme_name}")
            self.stateChanged.emit()
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as exc:
            self._set_status(f"Apply failed: {exc}")

    @Slot()
    def saveAndApply(self) -> None:
        if not self._editor:
            return
        try:
            path = self._editor.save(apply=False)
            theme_runtime.apply_saved_theme(self._editor.theme_name)
            self._preview_active = False
            self._restore_name = self._editor.theme_name
            self._effects_snapshot = self._read_effects_profile()
            self._effects_modified = False
            self._ui_override_snapshot = theme_ui.override_name()
            self._ui_override_modified = False
            self._set_status(f"Saved & applied {path.name}")
            self.stateChanged.emit()
            self.themesChanged.emit()
        except EditorError as exc:
            self._set_status(str(exc))
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as exc:
            self._set_status(f"Save/apply failed: {exc}")

    @Slot()
    def cancelChanges(self) -> None:
        if not self._editor:
            return
        try:
            self._restore_ui_override()
            self._editor.cancel()
            if self._preview_active:
                self._restore(self._editor.theme_name)
            if self._restore_effect_overrides() and self._restore_name:
                theme_runtime.apply_saved_theme(self._restore_name)
            self._set_status("Changes cancelled; desktop restored")
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as exc:
            self._set_status(f"Restore failed: {exc}")
        self.stateChanged.emit()

    @Slot()
    def reloadThemes(self) -> None:
        self.themesChanged.emit()
        self._set_status("Theme list refreshed")

    @Slot()
    def refreshWallpapers(self) -> None:
        self._wallpaper_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(
            (
                path
                for path in self._wallpaper_dir.iterdir()
                if path.is_file() and path.suffix.lower() in _WALLPAPER_EXTENSIONS
            ),
            key=lambda path: path.name.casefold(),
        )
        previous = self.selectedWallpaperName
        self._wallpapers = [
            {
                "name": path.name,
                "path": str(path),
                "url": QUrl.fromLocalFile(str(path)).toString(),
            }
            for path in files
        ]
        self._selected_wallpaper = next(
            (
                index
                for index, item in enumerate(self._wallpapers)
                if item["name"] == previous
            ),
            0 if self._wallpapers else -1,
        )
        self.wallpapersChanged.emit()
        self.selectedWallpaperChanged.emit()
        self._set_status(
            f"{len(self._wallpapers)} wallpaper{'s' if len(self._wallpapers) != 1 else ''} in {self._wallpaper_dir}"
        )

    @Slot(str)
    def setWallpaperDirectory(self, directory: str) -> None:
        path = Path(directory).expanduser()
        if not path.is_dir():
            self._set_status(f"Wallpaper folder does not exist: {path}")
            return
        self._wallpaper_dir = path.resolve()
        self.refreshWallpapers()

    @Slot(int)
    def selectWallpaper(self, index: int) -> None:
        if not self._wallpapers:
            return
        self._selected_wallpaper = max(0, min(index, len(self._wallpapers) - 1))
        # A recolor preview belongs to a particular source image.  Do not leave
        # it displayed after the user moves to a different wallpaper.
        self._template_name = ""
        self._regions = []
        self._recolor_preview_url = ""
        self._recolor_preview_theme = ""
        self.selectedWallpaperChanged.emit()
        self.recolorChanged.emit()
        self._set_status(f"Selected {self.selectedWallpaperName}")

    def _selected_wallpaper_path(self) -> Path | None:
        if not (0 <= self._selected_wallpaper < len(self._wallpapers)):
            return None
        return Path(self._wallpapers[self._selected_wallpaper]["path"])

    def _wallgen(
        self, *args: str, timeout: int = 60
    ) -> subprocess.CompletedProcess[str]:
        command = shutil.which("wallgen")
        if not command:
            raise OSError("wallgen is not installed; re-run install.sh")
        return subprocess.run(
            [command, *args],
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )

    def _template_path(self) -> Path | None:
        if not self._template_name:
            return None
        return (
            theme_runtime.CFG
            / "theme-engine"
            / "wallpaper-templates"
            / self._template_name
            / "template.json"
        )

    def _load_recolor_template(self, name: str) -> bool:
        self._template_name = name
        path = self._template_path()
        try:
            payload = json.loads(path.read_text(encoding="utf-8")) if path else {}
            self._regions = [
                {
                    "source": str(item.get("source", "")),
                    "role": str(item.get("role", "accent")),
                }
                for item in payload.get("regions", [])
                if isinstance(item, dict)
            ]
            self.recolorChanged.emit()
            return bool(self._regions)
        except (OSError, json.JSONDecodeError) as exc:
            self._set_status(f"Could not load recolor template: {exc}")
            return False

    def _save_recolor_regions(self) -> bool:
        path = self._template_path()
        if not path:
            return False
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["regions"] = self._regions
            fd, temporary = tempfile.mkstemp(
                prefix=".wallpaper-template-", suffix=".json", dir=path.parent
            )
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
                handle.write("\n")
            os.replace(temporary, path)
            return True
        except (OSError, json.JSONDecodeError) as exc:
            self._set_status(f"Could not save recolor mappings: {exc}")
            return False

    def _bind_wallpaper_path(self, path: Path, theme: str) -> bool:
        if theme not in list_themes():
            self._set_status(f"Unknown theme: {theme}")
            return False
        image = QImage(str(path))
        if image.isNull():
            self._set_status(f"Could not decode {path.name}")
            return False
        destination = theme_runtime.CFG / "hypr" / "wallpapers" / f"{theme}.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(
            prefix=f".{theme}.", suffix=".png", dir=destination.parent
        )
        os.close(fd)
        temporary_path = Path(temporary)
        try:
            if not image.save(str(temporary_path)):
                raise OSError("Qt could not encode the image as PNG")
            os.replace(temporary_path, destination)
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as exc:
            temporary_path.unlink(missing_ok=True)
            self._set_status(f"Could not bind wallpaper: {exc}")
            return False
        return True

    @Slot()
    def applySelectedWallpaper(self) -> None:
        path = self._selected_wallpaper_path()
        if not path:
            self._set_status("Select a wallpaper first")
            return
        try:
            theme_runtime.apply_wallpaper_path(path)
            self._set_status(
                f"Applied {path.name}; it is an override until the next theme switch"
            )
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
        ) as exc:
            self._set_status(f"Could not apply wallpaper: {exc}")

    @Slot(str)
    def bindSelectedWallpaper(self, theme: str) -> None:
        path = self._selected_wallpaper_path()
        if not path:
            self._set_status("Select a wallpaper first")
            return
        if self._bind_wallpaper_path(path, theme):
            self._set_status(
                f"Bound {path.name} to {theme}; it will apply when that theme is selected"
            )

    @Slot()
    def importSelectedForRecolor(self) -> None:
        path = self._selected_wallpaper_path()
        if not path:
            self._set_status("Select a wallpaper first")
            return
        name = (
            re.sub(r"[^a-z0-9_-]+", "-", path.stem.lower()).strip("-_") or "wallpaper"
        )
        try:
            args = ["semantic", "import", str(path), "--name", name, "--yes"]
            if self._current_theme_name():
                args.extend(("--palette", self._current_theme_name()))
            proc = self._wallgen(*args)
            if proc.returncode:
                self._set_status(
                    (proc.stderr or proc.stdout or "wallgen import failed").strip()
                )
                return
            if self._load_recolor_template(name):
                self._recolor_preview_url = ""
                self._recolor_preview_theme = ""
                self.recolorChanged.emit()
                self._set_status(
                    f"Detected {len(self._regions)} semantic color regions"
                )
        except (OSError, subprocess.SubprocessError) as exc:
            self._set_status(f"Could not import wallpaper: {exc}")

    @Slot(int, str)
    def setRecolorRole(self, index: int, role: str) -> None:
        if not (0 <= index < len(self._regions)) or role not in _SEMANTIC_ROLES:
            return
        self._regions[index] = {**self._regions[index], "role": role}
        if self._save_recolor_regions():
            self._recolor_preview_url = ""
            self._recolor_preview_theme = ""
            self.recolorChanged.emit()

    @Slot(str)
    def previewRecolor(self, theme: str) -> None:
        if not self._template_name or theme not in list_themes():
            self._set_status("Import a wallpaper and choose a valid theme first")
            return
        try:
            self._wallgen("semantic", "use", self._template_name)
            proc = self._wallgen("semantic", "apply", theme)
            if proc.returncode:
                self._set_status(
                    (proc.stderr or proc.stdout or "wallgen render failed").strip()
                )
                return
            output = Path((proc.stdout or "").strip().splitlines()[-1]).expanduser()
            if not output.is_file():
                self._set_status("wallgen did not return a rendered wallpaper")
                return
            self._recolor_preview_url = QUrl.fromLocalFile(
                str(output.resolve())
            ).toString()
            self._recolor_preview_theme = theme
            self.recolorChanged.emit()
            self._set_status(f"Previewing {self._template_name} with {theme}")
        except (OSError, subprocess.SubprocessError, IndexError) as exc:
            self._set_status(f"Could not preview recolor: {exc}")

    @Slot(str)
    def bindRecolorToTheme(self, theme: str) -> None:
        if not self._recolor_preview_url or self._recolor_preview_theme != theme:
            self.previewRecolor(theme)
        path = (
            Path(QUrl(self._recolor_preview_url).toLocalFile())
            if self._recolor_preview_url
            else None
        )
        if path and self._bind_wallpaper_path(path, theme):
            self._set_status(f"Bound recolored {self._template_name} to {theme}")

    @Slot()
    def closeSession(self) -> None:
        if not self._editor:
            return
        try:
            self._restore_ui_override()
            if self._preview_active:
                self._restore(self._editor.theme_name)
            else:
                theme_runtime.cleanup_preview()
            if self._restore_effect_overrides() and self._restore_name:
                theme_runtime.apply_saved_theme(self._restore_name)
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
        ):
            theme_runtime.cleanup_preview()
