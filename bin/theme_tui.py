"""Beautiful, keyboard-first curses interface for Theme Studio.

The app deliberately uses progressive disclosure:
Home -> Quick Style -> Components -> Advanced Inspector.
"""

from __future__ import annotations

import curses
import json
import os
import subprocess
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

import theme_runtime
from theme_editor import (
    EditorError,
    ThemeEditor,
    delete_theme,
    duplicate_theme,
    list_themes,
    load_theme,
    rename_theme,
)
from theme_preview import (
    component_preview,
    palette_preview,
    waybar_preview,
    window_preview,
)
from theme_schema import (
    ALL_ROLES,
    ANIMATION_PRESETS,
    BORDER_PRESETS,
    COMPONENT_FIELDS,
    COMPONENT_LABELS,
    DENSITY_PRESETS,
    ROLE_LABELS,
    SHAPE_PRESETS,
    SPACING_PRESETS,
    TEXTURE_PRESETS,
    WAYBAR_LAYOUT_PRESETS,
    WINDOW_PRESETS,
    FieldSpec,
    apply_axis,
    apply_window_preset,
    color_variants,
    contrast_ratio,
    deep_get,
    deep_set,
    ensure_theme_schema,
    extract_wallpaper_palette,
    generate_palette_from_seed,
    is_hex,
    palette_from_wallpaper,
    resolve_roles,
    safe_theme_name,
    search_index,
    validation_summary,
)
from theme_tui_widgets import (
    Palette,
    confirm,
    draw_box,
    draw_footer,
    draw_header,
    draw_list,
    fill_line,
    init_palette,
    message,
    prompt,
    safe_addstr,
    slider_text,
)

HOME_ITEMS = (
    ("Customize Current", "Adjust the vibe without touching raw config"),
    ("Browse Themes", "Preview and open any installed theme"),
    ("From Wallpaper", "Extract a palette from an image"),
    ("Manage Themes", "Duplicate, rename, compare, or archive"),
    ("Shell Style", "Browse, edit, and create Quickshell UI styles"),
)

QUICK_AXES = (
    ("Palette", "palette", ()),
    ("Shape", "shape", tuple(SHAPE_PRESETS)),
    ("Texture", "texture", tuple(TEXTURE_PRESETS)),
    ("Spacing", "spacing", tuple(SPACING_PRESETS)),
    ("Borders", "border", tuple(BORDER_PRESETS)),
    ("Waybar", "waybar", tuple(WAYBAR_LAYOUT_PRESETS)),
    ("Density", "density", tuple(DENSITY_PRESETS)),
    ("Animation", "animation", tuple(ANIMATION_PRESETS)),
)


class ThemeStudio:
    def __init__(self, theme_dir: Path | None = None):
        self.theme_dir = Path(theme_dir or theme_runtime.THEME_DIR).expanduser()
        self.palette = Palette()
        self.status = "Ready"
        self.home_selected = 0
        self.current_name = (
            os.environ.get("THEME_STUDIO_THEME") or theme_runtime.active_theme()
        )
        self.editor: ThemeEditor | None = None
        self.original_active = self.current_name
        self.last_preview_at = 0.0
        self.preview_error: str | None = None
        self.search_items = search_index()

    # ── lifecycle ──────────────────────────────────────────────────────
    def run(self, stdscr: Any) -> None:
        curses.curs_set(0)
        stdscr.keypad(True)
        try:
            curses.set_escdelay(25)
        except AttributeError:
            pass
        self.palette = init_palette()
        if not self.current_name:
            themes = list_themes(self.theme_dir)
            self.current_name = themes[0] if themes else None
        recoveries = ThemeEditor.recoveries()
        if recoveries and confirm(
            stdscr,
            "Recover draft",
            "A Theme Studio draft was found. Recover it?",
            self.palette,
        ):
            rec = recoveries[0]
            self.editor = ThemeEditor.from_recovery(
                rec, self.theme_dir, self._preview_callback, self._restore_callback
            )
            self.current_name = self.editor.theme_name
            self.quick_style(stdscr)
        while True:
            action = self.home(stdscr)
            if action == "quit":
                break
            if action == "customize":
                if self._ensure_editor(stdscr, self.current_name):
                    self.quick_style(stdscr)
            elif action == "browse":
                chosen = self.theme_browser(stdscr)
                if chosen and self._ensure_editor(stdscr, chosen):
                    self.quick_style(stdscr)
            elif action == "wallpaper":
                self.wallpaper_studio(stdscr)
            elif action == "manage":
                self.theme_manager(stdscr)
            elif action == "shell_style":
                self.shell_style_studio(stdscr)
        if self.editor and self.editor.dirty:
            if confirm(
                stdscr,
                "Unsaved changes",
                "Quit and discard the current draft?",
                self.palette,
            ):
                self.editor.cancel()
            else:
                self.run(stdscr)

    def _ensure_editor(self, stdscr: Any, name: str | None) -> bool:
        if not name:
            message(
                stdscr, "No themes", ["Install or create a theme first."], self.palette
            )
            return False
        if self.editor and self.editor.theme_name == name:
            return True
        if self.editor and self.editor.dirty:
            if not confirm(
                stdscr,
                "Discard draft",
                "Open another theme and discard unsaved changes?",
                self.palette,
            ):
                return False
            self.editor.cancel()
        try:
            self.editor = ThemeEditor(
                name, self.theme_dir, self._preview_callback, self._restore_callback
            )
            self.current_name = name
            self.original_active = theme_runtime.active_theme() or name
            self.status = f"Editing {name}"
            return True
        except EditorError as exc:
            message(
                stdscr,
                "Could not open theme",
                [str(exc)],
                self.palette,
                self.palette.error,
            )
            return False

    def _preview_callback(self, data: dict[str, Any], reason: str) -> None:
        now = time.monotonic()
        if now - self.last_preview_at < 0.12:
            return
        self.last_preview_at = now
        try:
            theme_runtime.preview_theme(data, reason)
            self.preview_error = None
            self.status = f"Desktop preview: {reason}"
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
            curses.error,
        ) as exc:
            self.preview_error = str(exc)
            self.status = "Desktop preview failed; mock preview still works"

    def _restore_callback(self, name: str) -> None:
        target = self.original_active or name
        try:
            theme_runtime.restore_theme(target)
            self.status = f"Restored {target}"
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
            curses.error,
        ) as exc:
            self.status = f"Restore warning: {exc}"

    # ── shared drawing ─────────────────────────────────────────────────
    def _theme_title(self) -> str:
        if not self.editor:
            return "THEME STUDIO"
        dirty = " •" if self.editor.dirty else ""
        return f"{self.editor.theme_name.upper()}{dirty}"

    def _status_right(self) -> str:
        if self.editor:
            live = "● LIVE" if self.editor.desktop_preview else "○ MOCK"
            changes = len(self.editor.undo_stack)
            return f"{live} · {changes} change{'s' if changes != 1 else ''}"
        return f"Current: {self.current_name or 'none'}"

    def _draw_status(self, stdscr: Any, y: int) -> None:
        _, width = stdscr.getmaxyx()
        attr = self.palette.error if self.preview_error else self.palette.muted
        safe_addstr(stdscr, y, 2, self.status, attr, width - 4)

    def _toggle_live_preview(self) -> None:
        if not self.editor:
            return
        try:
            self.editor.set_desktop_preview(not self.editor.desktop_preview)
            self.status = (
                "Live desktop preview enabled"
                if self.editor.desktop_preview
                else "Returned to mock-only preview"
            )
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
            curses.error,
        ) as exc:
            self.status = f"Preview error: {exc}"

    def _common_key(self, stdscr: Any, key: int) -> bool:
        if not self.editor:
            return False
        if key in (ord("u"), ord("U")):
            label = self.editor.undo()
            self.status = f"Undid {label}" if label else "Nothing to undo"
            return True
        if key == 18:  # Ctrl+r
            label = self.editor.redo()
            self.status = f"Redid {label}" if label else "Nothing to redo"
            return True
        if key in (ord("s"), ord("S")):
            self.save_dialog(stdscr)
            return True
        if key == ord("/"):
            self.search(stdscr)
            return True
        if key == ord("?"):
            self.help(stdscr)
            return True
        return False

    # ── home ───────────────────────────────────────────────────────────
    def home(self, stdscr: Any) -> str:
        selected = self.home_selected
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr,
                "THEME STUDIO",
                f"Current: {self.current_name or 'none'}",
                self.palette,
            )
            if width < 58 or height < 25:
                safe_addstr(
                    stdscr,
                    3,
                    2,
                    "Make your desktop feel like yours.",
                    curses.A_BOLD,
                    width - 4,
                )
                labels = [
                    f"{idx + 1}. {name} — {desc}"
                    for idx, (name, desc) in enumerate(HOME_ITEMS)
                ]
                draw_list(
                    stdscr, 5, 2, height - 9, width - 4, labels, selected, self.palette
                )
            else:
                safe_addstr(
                    stdscr, 3, 4, "Make your desktop feel like yours.", curses.A_BOLD
                )
                card_w = min(32, (width - 10) // 2)
                card_h = 6
                positions = [
                    (5 + (idx // 2) * 7, 4 + (idx % 2) * (2 + card_w))
                    for idx in range(len(HOME_ITEMS))
                ]
                for idx, ((name, desc), (y, x)) in enumerate(
                    zip(HOME_ITEMS, positions)
                ):
                    attr = (
                        self.palette.accent if idx == selected else self.palette.muted
                    )
                    draw_box(stdscr, y, x, card_h, card_w, f"{idx + 1}  {name}", attr)
                    safe_addstr(stdscr, y + 2, x + 2, desc, 0, card_w - 4)
                    if idx == selected:
                        safe_addstr(
                            stdscr,
                            y + 4,
                            x + 2,
                            "Enter to open",
                            self.palette.accent,
                            card_w - 4,
                        )
            draw_footer(
                stdscr,
                "↑↓←→ Move   Enter Open   / Search   ? Help   q Quit",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if key in (ord("q"), ord("Q"), 27):
                self.home_selected = selected
                return "quit"
            if key in (curses.KEY_RIGHT, ord("l")):
                selected = min(len(HOME_ITEMS) - 1, selected + 1)
            elif key in (curses.KEY_LEFT, ord("h")):
                selected = max(0, selected - 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                selected = min(
                    len(HOME_ITEMS) - 1,
                    selected + (2 if width >= 58 and height >= 25 else 1),
                )
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - (2 if width >= 58 and height >= 25 else 1))
            elif key in (ord("1"), ord("2"), ord("3"), ord("4"), ord("5")):
                selected = key - ord("1")
                key = 10
            if key in (10, 13):
                self.home_selected = selected
                return ("customize", "browse", "wallpaper", "manage", "shell_style")[
                    selected
                ]
            if key == ord("/"):
                self.search(stdscr)

    # ── browse ─────────────────────────────────────────────────────────
    def theme_browser(self, stdscr: Any) -> str | None:
        themes = list_themes(self.theme_dir)
        if not themes:
            message(
                stdscr,
                "No themes",
                [f"No JSON themes found in {self.theme_dir}"],
                self.palette,
            )
            return None
        selected = themes.index(self.current_name) if self.current_name in themes else 0
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr, "BROWSE THEMES", f"{len(themes)} installed", self.palette
            )
            split = max(24, min(38, width // 3))
            draw_box(stdscr, 3, 1, height - 6, split, "THEMES", self.palette.muted)
            draw_list(
                stdscr, 5, 3, height - 10, split - 4, themes, selected, self.palette
            )
            try:
                theme = load_theme(themes[selected], self.theme_dir)
                x = split + 3
                preview_w = max(20, width - x - 2)
                draw_box(
                    stdscr,
                    3,
                    x,
                    height - 6,
                    preview_w,
                    themes[selected],
                    self.palette.accent,
                )
                preview = window_preview(
                    theme, min(42, preview_w - 4), min(13, height - 11)
                )
                for idx, line in enumerate(preview):
                    safe_addstr(stdscr, 5 + idx, x + 2, line, 0, preview_w - 4)
                roles = resolve_roles(theme.get("roles", {}))
                y = min(height - 9, 6 + len(preview))
                safe_addstr(
                    stdscr,
                    y,
                    x + 2,
                    f"Accent {roles['accent']}  Surface {roles['bg_alt']}",
                    self.palette.muted,
                    preview_w - 4,
                )
            except (
                OSError,
                ValueError,
                TypeError,
                KeyError,
                RuntimeError,
                subprocess.SubprocessError,
                curses.error,
            ) as exc:
                safe_addstr(
                    stdscr,
                    5,
                    split + 5,
                    str(exc),
                    self.palette.error,
                    width - split - 7,
                )
            draw_footer(
                stdscr,
                "↑↓ Preview   Enter Customize   Space Apply now   Esc Back",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q")):
                return None
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(themes) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key in (10, 13):
                return themes[selected]
            elif key == ord(" "):
                try:
                    theme_runtime.apply_saved_theme(themes[selected])
                    self.current_name = themes[selected]
                    self.status = f"Applied {themes[selected]}"
                except (
                    OSError,
                    ValueError,
                    TypeError,
                    KeyError,
                    RuntimeError,
                    subprocess.SubprocessError,
                    curses.error,
                ) as exc:
                    self.status = f"Apply failed: {exc}"
            elif key == ord("/"):
                query = prompt(stdscr, "Find theme", "", palette=self.palette)
                if query:
                    matches = [
                        i
                        for i, name in enumerate(themes)
                        if query.lower() in name.lower()
                    ]
                    if matches:
                        selected = matches[0]

    # ── quick style ────────────────────────────────────────────────────
    def quick_style(self, stdscr: Any) -> None:
        if not self.editor:
            return
        axis = 0
        option_index: dict[str, int] = {}
        detail = False
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr,
                f"{self._theme_title()} / QUICK STYLE",
                self._status_right(),
                self.palette,
            )
            wide = width >= 92
            if wide:
                left_w = max(20, width // 4)
                mid_w = max(32, width // 3)
                preview_x = left_w + mid_w + 3
                draw_box(stdscr, 3, 1, height - 7, left_w, "LOOK", self.palette.muted)
                draw_box(
                    stdscr,
                    3,
                    left_w + 1,
                    height - 7,
                    mid_w + 1,
                    "ADJUST",
                    self.palette.muted,
                )
                draw_box(
                    stdscr,
                    3,
                    preview_x,
                    height - 7,
                    width - preview_x - 1,
                    "PREVIEW",
                    self.palette.muted,
                )
                self._draw_quick_axes(
                    stdscr, axis, option_index, detail, 5, 3, height - 11, left_w - 4
                )
                self._draw_quick_summary(stdscr, left_w + 4, 5, mid_w - 5)
                self._draw_quick_preview(
                    stdscr, preview_x + 2, 5, width - preview_x - 5, height - 11
                )
            else:
                draw_box(
                    stdscr,
                    3,
                    1,
                    height - 7,
                    width - 2,
                    "QUICK STYLE",
                    self.palette.muted,
                )
                self._draw_quick_axes(
                    stdscr, axis, option_index, detail, 5, 3, height - 12, width - 6
                )
                if width >= 58:
                    self._draw_quick_summary(stdscr, width // 2, 5, width // 2 - 4)
            self._draw_status(stdscr, height - 4)
            draw_footer(
                stdscr,
                "↑↓ Section  ←→ Change  Enter Open  Space Live  Tab Components  A Advanced  S Save  U Undo  Esc Back",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if self._common_key(stdscr, key):
                continue
            if key in (27, ord("q")):
                if self.editor.dirty and not confirm(
                    stdscr,
                    "Leave editor",
                    "Return home with this draft still open?",
                    self.palette,
                    True,
                ):
                    continue
                return
            if key in (curses.KEY_DOWN, ord("j")):
                axis = min(len(QUICK_AXES) - 1, axis + 1)
            elif key in (curses.KEY_UP, ord("k")):
                axis = max(0, axis - 1)
            elif key in (curses.KEY_LEFT, ord("h"), curses.KEY_RIGHT, ord("l")):
                direction = -1 if key in (curses.KEY_LEFT, ord("h")) else 1
                self._change_quick_axis(axis, direction, option_index)
            elif key == ord(" "):
                self._toggle_live_preview()
            elif key == 9:
                detail = not detail
                if detail:
                    self.components(stdscr)
            elif key in (10, 13):
                if axis == 0:
                    self.palette_editor(stdscr)
                else:
                    self.components(stdscr)
            elif key in (ord("a"), ord("A")):
                self.advanced_inspector(stdscr)
            elif key in (ord("r"), ord("R")):
                if confirm(
                    stdscr,
                    "Reset Quick Style",
                    "Reset all theme changes to the original?",
                    self.palette,
                ):
                    self.editor.reset_all()
                    self.status = "Theme reset"
            elif key in (ord("p"), ord("P")):
                self.window_preset_picker(stdscr)

    def _draw_quick_axes(
        self,
        stdscr: Any,
        selected: int,
        indexes: dict[str, int],
        detail: bool,
        y: int,
        x: int,
        height: int,
        width: int,
    ) -> None:
        assert self.editor
        theme = self.editor.draft
        row = y
        for idx, (label, key, choices) in enumerate(QUICK_AXES):
            if row >= y + height:
                break
            attr = (
                self.palette.selected
                if idx == selected
                else (self.palette.accent if idx == selected else 0)
            )
            current = self._quick_current(theme, key)
            fill_line(stdscr, row, x, width, " ", attr)
            safe_addstr(stdscr, row, x, f"{label:<11} {current}", attr, width)
            if idx == selected and row + 1 < y + height:
                if key == "palette":
                    roles = resolve_roles(theme.get("roles", {}))
                    hint = f"accent {roles['accent']} · bg {roles['bg']}"
                else:
                    hint = "← / → to change"
                safe_addstr(stdscr, row + 1, x + 2, hint, self.palette.muted, width - 2)
                row += 1
            row += 2
        if detail:
            safe_addstr(
                stdscr,
                min(y + height - 1, row),
                x,
                "Fine Tune mode",
                self.palette.warning,
                width,
            )

    def _draw_quick_summary(self, stdscr: Any, x: int, y: int, width: int) -> None:
        assert self.editor
        theme = self.editor.draft
        win = theme["components"]["windows"]
        bar = theme["components"]["waybar"]
        summary = [
            "CURRENT FEEL",
            f"Spacing       {theme['style'].get('spacing_preset', 'custom')}",
            f"Corners       {win.get('corner_radius')} px",
            f"Blur          {'On' if win['blur'].get('enabled') else 'Off'} · {win['blur'].get('size')}",
            f"Border        {win.get('border_width')} px · {theme['style'].get('border_preset', 'custom')}",
            f"Glass         {float(win.get('active_opacity', 1)):.2f}",
            f"Waybar        {bar.get('layout')} · {bar.get('height')} px",
            f"Animation     {theme['style'].get('animation_preset', 'smooth')}",
            "",
            "Enter opens component rooms.",
            "Tab reveals fine controls.",
        ]
        for idx, line in enumerate(summary):
            safe_addstr(
                stdscr, y + idx, x, line, self.palette.accent if idx == 0 else 0, width
            )

    def _draw_quick_preview(
        self, stdscr: Any, x: int, y: int, width: int, height: int
    ) -> None:
        assert self.editor
        lines = window_preview(
            self.editor.draft, max(20, min(width, 38)), max(9, min(height - 5, 13))
        )
        for idx, line in enumerate(lines[: max(0, height - 4)]):
            safe_addstr(stdscr, y + idx, x, line, 0, width)
        bar_y = min(y + len(lines) + 1, y + height - 2)
        for idx, line in enumerate(waybar_preview(self.editor.draft, max(20, width))):
            safe_addstr(stdscr, bar_y + idx, x, line, self.palette.accent, width)

    def _quick_current(self, theme: dict[str, Any], key: str) -> str:
        if key == "palette":
            return theme.get(
                "name", self.editor.theme_name if self.editor else "Custom"
            )
        if key == "waybar":
            return (
                str(deep_get(theme, "components.waybar.layout", "islands"))
                .replace("_", " ")
                .title()
            )
        return (
            str(theme.get("style", {}).get(f"{key}_preset", "custom"))
            .replace("_", " ")
            .title()
        )

    def _change_quick_axis(
        self, axis: int, direction: int, indexes: dict[str, int]
    ) -> None:
        assert self.editor
        label, key, choices = QUICK_AXES[axis]
        if key == "palette":
            return
        current = self._quick_current(self.editor.draft, key).lower().replace(" ", "_")
        values = list(choices)
        try:
            index = values.index(current)
        except ValueError:
            index = indexes.get(key, 0)
        index = (index + direction) % len(values)
        indexes[key] = index
        name = values[index]
        self.editor.mutate(f"Set {label} to {name}", lambda d: apply_axis(d, key, name))
        self.status = f"{label}: {name.replace('_', ' ').title()}"

    # ── components ─────────────────────────────────────────────────────
    def components(self, stdscr: Any) -> None:
        if not self.editor:
            return
        components = list(COMPONENT_LABELS)
        selected = 0
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr,
                f"{self._theme_title()} / COMPONENTS",
                self._status_right(),
                self.palette,
            )
            left_w = min(26, max(18, width // 4))
            draw_box(stdscr, 3, 1, height - 7, left_w, "COMPONENTS", self.palette.muted)
            draw_list(
                stdscr,
                5,
                3,
                height - 11,
                left_w - 4,
                [COMPONENT_LABELS[c] for c in components],
                selected,
                self.palette,
            )
            x = left_w + 3
            draw_box(
                stdscr, 3, x, height - 7, width - x - 1, "ROOM", self.palette.muted
            )
            name = components[selected]
            safe_addstr(
                stdscr,
                5,
                x + 2,
                COMPONENT_LABELS[name],
                self.palette.accent,
                width - x - 5,
            )
            descriptions = {
                "windows": "Gaps, borders, corners, opacity, blur, shadows, animation.",
                "waybar": "Layout, modules, spacing, workspace states, clock, battery.",
                "launcher": "Wofi/Rofi search surface, rows, padding, selection.",
                "notifications": "Dunst position, size, urgency colors, timeout.",
                "terminal": "Kitty opacity, padding, tabs, cursor, selection.",
                "prompt": "Starship layout, separators, modules, status roles.",
                "lock_screen": "Hyprlock clock, password field, avatar, colors.",
                "homepage": "Cards, alignment, visibility, density, glass.",
                "apps": "GTK, Qt, Firefox, VS Code and common UI states.",
            }
            safe_addstr(stdscr, 7, x + 2, descriptions[name], 0, width - x - 5)
            preview = component_preview(
                self.editor.draft, name, min(44, width - x - 5), min(14, height - 13)
            )
            for idx, line in enumerate(preview):
                safe_addstr(stdscr, 10 + idx, x + 2, line, 0, width - x - 5)
            self._draw_status(stdscr, height - 4)
            draw_footer(
                stdscr,
                "↑↓ Choose room   Enter Edit   P Palette   A Advanced   Space Live   / Search   Esc Quick Style",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if self._common_key(stdscr, key):
                continue
            if key in (27, ord("q")):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(components) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key == ord(" "):
                self._toggle_live_preview()
            elif key in (ord("p"), ord("P")):
                self.palette_editor(stdscr)
            elif key in (ord("a"), ord("A")):
                self.advanced_inspector(stdscr)
            elif key in (10, 13):
                if name == "waybar":
                    self.waybar_editor(stdscr)
                else:
                    self.component_editor(stdscr, name)

    def component_editor(
        self, stdscr: Any, component: str, jump_path: str | None = None
    ) -> None:
        if not self.editor:
            return
        fields = list(COMPONENT_FIELDS.get(component, ()))
        selected = next((i for i, f in enumerate(fields) if f.path == jump_path), 0)
        advanced = False
        while True:
            visible = [f for f in fields if advanced or not f.advanced]
            if selected >= len(visible):
                selected = max(0, len(visible) - 1)
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr,
                f"COMPONENTS / {COMPONENT_LABELS[component].upper()}",
                self._status_right(),
                self.palette,
            )
            wide = width >= 82
            controls_w = width - 3 if not wide else max(42, width // 2)
            draw_box(
                stdscr, 3, 1, height - 7, controls_w, "FINE TUNE", self.palette.muted
            )
            start = max(0, selected - max(1, (height - 12) // 2))
            row = 5
            for idx in range(start, min(len(visible), start + height - 11)):
                field = visible[idx]
                value = deep_get(self.editor.draft, field.path)
                attr = self.palette.selected if idx == selected else 0
                fill_line(stdscr, row, 3, controls_w - 4, " ", attr)
                safe_addstr(stdscr, row, 3, field.label, attr, max(16, controls_w // 2))
                rendered = self._render_field(
                    field, value, max(12, controls_w // 2 - 3)
                )
                safe_addstr(
                    stdscr,
                    row,
                    3 + max(16, controls_w // 2),
                    rendered,
                    attr,
                    controls_w // 2 - 4,
                )
                row += 1
            if wide:
                x = controls_w + 2
                draw_box(
                    stdscr,
                    3,
                    x,
                    height - 7,
                    width - x - 1,
                    "LIVE MOCK PREVIEW",
                    self.palette.muted,
                )
                preview = component_preview(
                    self.editor.draft, component, width - x - 5, height - 11
                )
                for idx, line in enumerate(preview):
                    safe_addstr(stdscr, 5 + idx, x + 2, line, 0, width - x - 5)
            self._draw_status(stdscr, height - 4)
            draw_footer(
                stdscr,
                "↑↓ Setting  ←→ Adjust  Enter Exact/Edit  Space Live  Tab Advanced  P Presets  R Reset  Esc Back",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if self._common_key(stdscr, key):
                continue
            if key in (27, ord("q")):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(visible) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif (
                key in (curses.KEY_LEFT, ord("h"), curses.KEY_RIGHT, ord("l"))
                and visible
            ):
                self._adjust_field(
                    visible[selected], -1 if key in (curses.KEY_LEFT, ord("h")) else 1
                )
            elif key in (10, 13) and visible:
                self._edit_field(stdscr, visible[selected])
            elif key == ord(" "):
                self._toggle_live_preview()
            elif key == 9:
                advanced = not advanced
                selected = 0
                self.status = (
                    "Advanced fields shown" if advanced else "Simple fields only"
                )
            elif key in (ord("r"), ord("R")):
                self.editor.reset_section(f"components.{component}")
                self.status = f"Reset {COMPONENT_LABELS[component]}"
            elif key in (ord("p"), ord("P")):
                if component == "windows":
                    self.window_preset_picker(stdscr)
                else:
                    self.status = "This room inherits Quick Style presets; adjust any field to override"

    def _render_field(self, field: FieldSpec, value: Any, width: int) -> str:
        if (
            field.kind in ("int", "float")
            and field.minimum is not None
            and field.maximum is not None
        ):
            return slider_text(
                float(value),
                field.minimum,
                field.maximum,
                max(6, width - 8),
                2 if field.kind == "float" else 0,
            )
        if field.kind == "bool":
            return "[ ON ]" if value else "[ off ]"
        if field.kind == "role":
            return (
                f"{value}  {resolve_roles(self.editor.draft.get('roles', {})).get(str(value), '')}"
                if self.editor
                else str(value)
            )
        return str(value)

    def _adjust_field(self, field: FieldSpec, direction: int) -> None:
        assert self.editor
        value = deep_get(self.editor.draft, field.path)
        if field.kind == "bool":
            new_value = not bool(value)
        elif field.kind in ("int", "float"):
            new_value = float(value) + field.step * direction
            if field.minimum is not None:
                new_value = max(field.minimum, new_value)
            if field.maximum is not None:
                new_value = min(field.maximum, new_value)
            if field.kind == "int":
                new_value = round(new_value)
            else:
                new_value = round(new_value, 4)
        elif field.kind == "choice":
            choices = list(field.choices)
            try:
                index = choices.index(value)
            except ValueError:
                index = 0
            new_value = choices[(index + direction) % len(choices)]
        elif field.kind == "role":
            roles = list(ALL_ROLES)
            try:
                index = roles.index(value)
            except ValueError:
                index = 0
            new_value = roles[(index + direction) % len(roles)]
        else:
            return
        self.editor.mutate(
            f"Change {field.label}", lambda d: deep_set(d, field.path, new_value)
        )
        self.status = f"{field.label}: {new_value}"

    def _edit_field(self, stdscr: Any, field: FieldSpec) -> None:
        assert self.editor
        current = deep_get(self.editor.draft, field.path)
        if field.kind in ("bool", "choice", "role"):
            self._adjust_field(field, 1)
            return
        value = prompt(stdscr, field.label, str(current), palette=self.palette)
        if value is None:
            return
        try:
            if field.kind == "int":
                parsed: Any = int(value)
            elif field.kind == "float":
                parsed = float(value)
            else:
                parsed = value
            if field.minimum is not None and parsed < field.minimum:
                raise ValueError(f"minimum {field.minimum}")
            if field.maximum is not None and parsed > field.maximum:
                raise ValueError(f"maximum {field.maximum}")
            self.editor.mutate(
                f"Set {field.label}", lambda d: deep_set(d, field.path, parsed)
            )
        except ValueError as exc:
            message(
                stdscr, "Invalid value", [str(exc)], self.palette, self.palette.error
            )

    def window_preset_picker(self, stdscr: Any) -> None:
        assert self.editor
        names = list(WINDOW_PRESETS)
        selected = 0
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(stdscr, "WINDOW PRESETS", self._status_right(), self.palette)
            split = min(32, width // 3)
            draw_box(
                stdscr, 3, 1, height - 6, split, "STARTING POINT", self.palette.muted
            )
            draw_list(
                stdscr,
                5,
                3,
                height - 10,
                split - 4,
                [n.replace("_", " ").title() for n in names],
                selected,
                self.palette,
            )
            x = split + 3
            draw_box(
                stdscr, 3, x, height - 6, width - x - 1, "PREVIEW", self.palette.muted
            )
            temp = deepcopy(self.editor.draft)
            apply_window_preset(temp, names[selected])
            for idx, line in enumerate(
                window_preview(temp, min(42, width - x - 5), min(14, height - 10))
            ):
                safe_addstr(stdscr, 5 + idx, x + 2, line, 0, width - x - 5)
            draw_footer(
                stdscr, "↑↓ Preview   Enter Use preset   Esc Cancel", self.palette
            )
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q")):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(names) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key in (10, 13):
                name = names[selected]
                self.editor.mutate(
                    f"Apply {name} window preset",
                    lambda d, name=name: apply_window_preset(d, name),
                )
                self.status = f"Window preset: {name.replace('_', ' ').title()}"
                return

    # ── waybar special editor ──────────────────────────────────────────
    def waybar_editor(self, stdscr: Any) -> None:
        assert self.editor
        pane = 0  # appearance / modules
        field_selected = 0
        side_selected = 0
        module_selected = 0
        sides = ["left", "center", "right"]
        fields = [
            f
            for f in COMPONENT_FIELDS["waybar"]
            if not f.path.startswith("components.waybar.workspace")
        ]
        while True:
            bar = self.editor.draft["components"]["waybar"]
            modules = bar["modules"].get(sides[side_selected], [])
            module_selected = max(0, min(module_selected, max(0, len(modules) - 1)))
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr,
                "COMPONENTS / WAYBAR",
                f"Layout: {bar.get('layout', 'islands').title()} · {self._status_right()}",
                self.palette,
            )
            left_w = max(32, width // 3)
            mid_w = max(28, width // 3)
            preview_x = left_w + mid_w + 3
            draw_box(
                stdscr,
                3,
                1,
                height - 7,
                left_w,
                "APPEARANCE",
                self.palette.accent if pane == 0 else self.palette.muted,
            )
            draw_box(
                stdscr,
                3,
                left_w + 1,
                height - 7,
                mid_w + 1,
                "MODULES",
                self.palette.accent if pane == 1 else self.palette.muted,
            )
            if preview_x < width - 12:
                draw_box(
                    stdscr,
                    3,
                    preview_x,
                    height - 7,
                    width - preview_x - 1,
                    "LIVE PREVIEW",
                    self.palette.muted,
                )
            # appearance fields
            row = 5
            start = max(0, field_selected - max(1, (height - 12) // 2))
            for idx in range(start, min(len(fields), start + height - 11)):
                field = fields[idx]
                value = deep_get(self.editor.draft, field.path)
                attr = (
                    self.palette.selected if pane == 0 and idx == field_selected else 0
                )
                fill_line(stdscr, row, 3, left_w - 4, " ", attr)
                safe_addstr(stdscr, row, 3, field.label, attr, left_w // 2 - 2)
                safe_addstr(
                    stdscr,
                    row,
                    3 + left_w // 2,
                    self._render_field(field, value, left_w // 2 - 5),
                    attr,
                    left_w // 2 - 5,
                )
                row += 1
            # modules
            x = left_w + 3
            safe_addstr(
                stdscr, 5, x, "H/L group · J/K module", self.palette.muted, mid_w - 4
            )
            group_line = "  ".join(
                f"[{s.upper()}]" if idx == side_selected else s.upper()
                for idx, s in enumerate(sides)
            )
            safe_addstr(stdscr, 7, x, group_line, self.palette.accent, mid_w - 4)
            draw_list(
                stdscr,
                9,
                x,
                height - 14,
                mid_w - 4,
                [m for m in modules] or ["(empty)"],
                module_selected,
                self.palette if pane == 1 else Palette(),
            )
            if preview_x < width - 12:
                for idx, line in enumerate(
                    waybar_preview(self.editor.draft, width - preview_x - 5)
                ):
                    safe_addstr(
                        stdscr,
                        6 + idx,
                        preview_x + 2,
                        line,
                        self.palette.accent,
                        width - preview_x - 5,
                    )
                safe_addstr(
                    stdscr,
                    10,
                    preview_x + 2,
                    "Space: toggle selected module",
                    self.palette.muted,
                    width - preview_x - 5,
                )
                safe_addstr(
                    stdscr,
                    11,
                    preview_x + 2,
                    "Shift+J/K: reorder",
                    self.palette.muted,
                    width - preview_x - 5,
                )
                safe_addstr(
                    stdscr,
                    12,
                    preview_x + 2,
                    "M: move to next group",
                    self.palette.muted,
                    width - preview_x - 5,
                )
                safe_addstr(
                    stdscr,
                    13,
                    preview_x + 2,
                    "A: add known module",
                    self.palette.muted,
                    width - preview_x - 5,
                )
                safe_addstr(
                    stdscr,
                    14,
                    preview_x + 2,
                    "O: per-module override",
                    self.palette.muted,
                    width - preview_x - 5,
                )
            self._draw_status(stdscr, height - 4)
            draw_footer(
                stdscr,
                "Tab Switch pane  Arrows Adjust  M Move  A Add  X Remove  O Override  Space Live  Esc Back",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if self._common_key(stdscr, key):
                continue
            if key in (27, ord("q")):
                return
            if key == 9:
                pane = 1 - pane
            elif key == ord(" ") and pane == 0:
                self._toggle_live_preview()
            elif pane == 0:
                if key in (curses.KEY_DOWN, ord("j")):
                    field_selected = min(len(fields) - 1, field_selected + 1)
                elif key in (curses.KEY_UP, ord("k")):
                    field_selected = max(0, field_selected - 1)
                elif key in (curses.KEY_LEFT, ord("h"), curses.KEY_RIGHT, ord("l")):
                    self._adjust_field(
                        fields[field_selected],
                        -1 if key in (curses.KEY_LEFT, ord("h")) else 1,
                    )
                elif key in (10, 13):
                    self._edit_field(stdscr, fields[field_selected])
                elif key in (ord("p"), ord("P")):
                    self._waybar_layout_picker(stdscr)
            else:
                if key in (curses.KEY_LEFT, ord("h")):
                    side_selected = max(0, side_selected - 1)
                    module_selected = 0
                elif key in (curses.KEY_RIGHT, ord("l")):
                    side_selected = min(2, side_selected + 1)
                    module_selected = 0
                elif key in (curses.KEY_DOWN, ord("j")):
                    module_selected = min(max(0, len(modules) - 1), module_selected + 1)
                elif key in (curses.KEY_UP, ord("k")):
                    module_selected = max(0, module_selected - 1)
                elif key == ord("J") and modules and module_selected < len(modules) - 1:
                    self._reorder_module(
                        sides[side_selected], module_selected, module_selected + 1
                    )
                    module_selected += 1
                elif key == ord("K") and modules and module_selected > 0:
                    self._reorder_module(
                        sides[side_selected], module_selected, module_selected - 1
                    )
                    module_selected -= 1
                elif key in (ord("m"), ord("M")) and modules:
                    target = (side_selected + 1) % 3
                    self._move_module(
                        sides[side_selected], sides[target], module_selected
                    )
                    side_selected = target
                    module_selected = 0
                elif key in (ord("x"), ord("X"), curses.KEY_DC) and modules:
                    self._remove_module(sides[side_selected], module_selected)
                    module_selected = max(0, module_selected - 1)
                elif key in (ord("a"), ord("A")):
                    self._add_module_dialog(stdscr, sides[side_selected])
                elif key in (ord("o"), ord("O")) and modules:
                    self._module_override_dialog(stdscr, modules[module_selected])
                elif key == ord(" "):
                    self._toggle_live_preview()

    def _waybar_layout_picker(self, stdscr: Any) -> None:
        assert self.editor
        names = list(WAYBAR_LAYOUT_PRESETS)
        selected = names.index(
            deep_get(self.editor.draft, "components.waybar.layout", "islands")
        )
        while True:
            stdscr.erase()
            _height, width = stdscr.getmaxyx()
            draw_header(stdscr, "WAYBAR LAYOUT", self._status_right(), self.palette)
            draw_list(
                stdscr,
                4,
                3,
                len(names),
                20,
                [n.title() for n in names],
                selected,
                self.palette,
            )
            temp = deepcopy(self.editor.draft)
            apply_axis(temp, "waybar", names[selected])
            for idx, line in enumerate(waybar_preview(temp, max(24, width - 30))):
                safe_addstr(stdscr, 6 + idx, 26, line, self.palette.accent, width - 28)
            draw_footer(
                stdscr, "↑↓ Preview  Enter Use layout  Esc Cancel", self.palette
            )
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q")):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(names) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key in (10, 13):
                name = names[selected]
                self.editor.mutate(
                    f"Set Waybar layout to {name}",
                    lambda d, name=name: apply_axis(d, "waybar", name),
                )
                return

    def _reorder_module(self, side: str, old: int, new: int) -> None:
        assert self.editor

        def mutate(data: dict[str, Any]) -> None:
            values = data["components"]["waybar"]["modules"][side]
            values.insert(new, values.pop(old))

        self.editor.mutate("Reorder Waybar module", mutate)

    def _move_module(self, source: str, target: str, index: int) -> None:
        assert self.editor

        def mutate(data: dict[str, Any]) -> None:
            groups = data["components"]["waybar"]["modules"]
            module = groups[source].pop(index)
            groups[target].append(module)

        self.editor.mutate(f"Move Waybar module to {target}", mutate)

    def _remove_module(self, side: str, index: int) -> None:
        assert self.editor

        def mutate(data: dict[str, Any]) -> None:
            data["components"]["waybar"]["modules"][side].pop(index)

        self.editor.mutate("Disable Waybar module", mutate)

    def _add_module_dialog(self, stdscr: Any, side: str) -> None:
        assert self.editor
        known = [
            "hyprland/workspaces",
            "hyprland/window",
            "custom/launcher",
            "clock",
            "network",
            "pulseaudio",
            "battery",
            "cpu",
            "memory",
            "temperature",
            "tray",
            "custom/vpn",
            "custom/sysstat",
            "custom/notifications",
            "custom/running-apps",
        ]
        present = [
            item
            for side_name in ("left", "center", "right")
            for item in self.editor.draft["components"]["waybar"]["modules"][side_name]
        ]
        choices = [m for m in known if m not in present]
        selected = 0
        while choices:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(stdscr, f"ADD MODULE TO {side.upper()}", "", self.palette)
            draw_list(
                stdscr, 4, 3, height - 8, width - 6, choices, selected, self.palette
            )
            draw_footer(stdscr, "↑↓ Choose  Enter Add  Esc Cancel", self.palette)
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q")):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(choices) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key in (10, 13):
                module = choices[selected]
                self.editor.mutate(
                    f"Add Waybar module {module}",
                    lambda d, module=module: d["components"]["waybar"]["modules"][
                        side
                    ].append(module),
                )
                return

    def _module_override_dialog(self, stdscr: Any, module: str) -> None:
        assert self.editor
        overrides = self.editor.draft["components"]["waybar"].setdefault(
            "module_overrides", {}
        )
        current = deepcopy(
            overrides.get(
                module,
                {
                    "enabled": False,
                    "background_role": "surface_0",
                    "text_role": "text",
                    "border_role": "border_subtle",
                    "opacity": 0.82,
                    "padding": 10,
                    "radius": 14,
                },
            )
        )
        fields = [
            ("enabled", "Separate style", "bool"),
            ("background_role", "Background role", "role"),
            ("text_role", "Text role", "role"),
            ("border_role", "Border role", "role"),
            ("opacity", "Opacity", "float"),
            ("padding", "Padding", "int"),
            ("radius", "Radius", "int"),
        ]
        selected = 0
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr, f"WAYBAR / {module}", "Per-module override", self.palette
            )
            draw_box(
                stdscr,
                3,
                2,
                height - 7,
                width - 4,
                "CUSTOMIZE THIS MODULE SEPARATELY?",
                self.palette.muted,
            )
            row = 5
            for idx, (key, label, kind) in enumerate(fields):
                attr = self.palette.selected if idx == selected else 0
                fill_line(stdscr, row, 4, width - 8, " ", attr)
                safe_addstr(stdscr, row, 4, label, attr, 28)
                safe_addstr(stdscr, row, 34, str(current[key]), attr, width - 38)
                row += 1
            draw_footer(
                stdscr, "↑↓ Field  ←→ Change  Enter Save  Esc Cancel", self.palette
            )
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q")):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(fields) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key in (curses.KEY_LEFT, ord("h"), curses.KEY_RIGHT, ord("l")):
                direction = -1 if key in (curses.KEY_LEFT, ord("h")) else 1
                name, _, kind = fields[selected]
                if kind == "bool":
                    current[name] = not current[name]
                elif kind == "role":
                    idx = (
                        list(ALL_ROLES).index(current[name])
                        if current[name] in ALL_ROLES
                        else 0
                    )
                    current[name] = ALL_ROLES[(idx + direction) % len(ALL_ROLES)]
                elif kind == "float":
                    current[name] = round(
                        max(0, min(1, float(current[name]) + 0.05 * direction)), 2
                    )
                else:
                    current[name] = max(0, int(current[name]) + direction)
            elif key in (10, 13):
                self.editor.mutate(
                    f"Style Waybar module {module}",
                    lambda d: (
                        d["components"]["waybar"]
                        .setdefault("module_overrides", {})
                        .__setitem__(module, deepcopy(current))
                    ),
                )
                return

    # ── palette ────────────────────────────────────────────────────────
    def palette_editor(self, stdscr: Any, jump_path: str | None = None) -> None:
        assert self.editor
        roles = list(ALL_ROLES)
        selected = 0
        if jump_path and jump_path.startswith("roles."):
            role = jump_path.split(".", 1)[1]
            if role in roles:
                selected = roles.index(role)
        locked = set(self.editor.draft.get("studio", {}).get("locks", []))
        while True:
            resolved = resolve_roles(self.editor.draft.get("roles", {}))
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            issues = self.editor.validate()
            errors, warnings = validation_summary(issues)
            health = (
                "GOOD"
                if not errors and not warnings
                else f"{errors} errors · {warnings} suggestions"
            )
            draw_header(
                stdscr,
                f"PALETTE STUDIO / {self.editor.theme_name.upper()}",
                f"Contrast: {health}",
                self.palette,
            )
            left_w = min(34, max(26, width // 3))
            draw_box(stdscr, 3, 1, height - 7, left_w, "COLORS", self.palette.muted)
            start = max(0, selected - max(1, (height - 12) // 2))
            row = 5
            for idx in range(start, min(len(roles), start + height - 11)):
                role = roles[idx]
                value = resolved.get(role, "#000000")
                attr = self.palette.selected if idx == selected else 0
                lock = "◆" if role in locked else " "
                fill_line(stdscr, row, 3, left_w - 4, " ", attr)
                safe_addstr(
                    stdscr,
                    row,
                    3,
                    f"{lock} {ROLE_LABELS.get(role, role):<18} {value}",
                    attr,
                    left_w - 4,
                )
                row += 1
            x = left_w + 3
            draw_box(
                stdscr,
                3,
                x,
                height - 7,
                width - x - 1,
                "SAMPLE & HEALTH",
                self.palette.muted,
            )
            role = roles[selected]
            value = resolved.get(role, "#000000")
            safe_addstr(
                stdscr,
                5,
                x + 2,
                ROLE_LABELS.get(role, role),
                self.palette.accent,
                width - x - 5,
            )
            safe_addstr(
                stdscr,
                7,
                x + 2,
                f"Role name: {role}",
                self.palette.muted,
                width - x - 5,
            )
            safe_addstr(stdscr, 8, x + 2, f"Value:     {value}", 0, width - x - 5)
            safe_addstr(
                stdscr,
                10,
                x + 2,
                f"On main background: {contrast_ratio(value, resolved['bg']):.2f}:1",
                0,
                width - x - 5,
            )
            safe_addstr(
                stdscr,
                11,
                x + 2,
                f"On raised surface:  {contrast_ratio(value, resolved['bg_alt']):.2f}:1",
                0,
                width - x - 5,
            )
            variant = color_variants(value)
            safe_addstr(
                stdscr,
                13,
                x + 2,
                "Generated variants",
                self.palette.accent,
                width - x - 5,
            )
            safe_addstr(
                stdscr,
                14,
                x + 2,
                "  ".join(f"{k}:{v}" for k, v in list(variant.items())[:4]),
                self.palette.muted,
                width - x - 5,
            )
            warn_y = 16
            for issue in [i for i in issues if i["path"].startswith("roles.")][
                : max(0, height - warn_y - 4)
            ]:
                attr = (
                    self.palette.error
                    if issue["level"] == "error"
                    else self.palette.warning
                )
                safe_addstr(
                    stdscr,
                    warn_y,
                    x + 2,
                    f"{issue['level'].upper()}: {issue['message']}",
                    attr,
                    width - x - 5,
                )
                warn_y += 1
            self._draw_status(stdscr, height - 4)
            draw_footer(
                stdscr,
                "↑↓ Role  E Edit  X Swap  L Lock  G Variants  C Check  I Import  O Export  Esc Back",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if self._common_key(stdscr, key):
                continue
            if key in (27, ord("q")):
                self.editor.draft.setdefault("studio", {})["locks"] = sorted(locked)
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(roles) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key in (ord("e"), ord("E"), 10, 13):
                entered = prompt(
                    stdscr,
                    f"Edit {ROLE_LABELS.get(role, role)}",
                    value,
                    palette=self.palette,
                )
                if entered is not None:
                    if is_hex(entered):
                        color = entered.lower()
                        self.editor.mutate(
                            f"Change color {role}",
                            lambda d, role=role, color=color: d["roles"].__setitem__(
                                role, color
                            ),
                        )
                    else:
                        message(
                            stdscr,
                            "Invalid color",
                            ["Use a six-digit hex color such as #ff5aa5."],
                            self.palette,
                            self.palette.error,
                        )
            elif key in (ord("l"), ord("L")):
                if role in locked:
                    locked.remove(role)
                else:
                    locked.add(role)
                self.editor.draft.setdefault("studio", {})["locks"] = sorted(locked)
            elif key in (ord("x"), ord("X")):
                other = prompt(
                    stdscr, "Swap with role", "accent2", palette=self.palette
                )
                if other in roles:
                    a, b = (
                        self.editor.draft["roles"].get(role, resolved[role]),
                        self.editor.draft["roles"].get(other, resolved[other]),
                    )

                    def swap_colors(
                        d: dict[str, Any],
                        role: str = role,
                        other: str = other,
                        a: str = a,
                        b: str = b,
                    ) -> None:
                        d["roles"][role] = b
                        d["roles"][other] = a

                    self.editor.mutate(f"Swap {role} and {other}", swap_colors)
            elif key in (ord("g"), ord("G")):
                variants = color_variants(value)
                names = list(variants)
                choice = self._simple_picker(
                    stdscr, "GENERATED VARIANTS", [f"{n}: {variants[n]}" for n in names]
                )
                if choice is not None:
                    new = variants[names[choice]]
                    self.editor.mutate(
                        f"Use {names[choice]} variant for {role}",
                        lambda d, role=role, new=new: d["roles"].__setitem__(role, new),
                    )
            elif key in (ord("c"), ord("C")):
                lines = [
                    f"{i['level'].upper()} · {i['message']}"
                    for i in issues
                    if i["path"].startswith("roles.")
                ] or ["All primary contrast checks pass."]
                message(stdscr, "Contrast report", lines, self.palette)
            elif key in (ord("i"), ord("I")):
                path = prompt(stdscr, "Import palette JSON", "", palette=self.palette)
                if path:
                    try:
                        data = json.loads(
                            Path(path).expanduser().read_text(encoding="utf-8")
                        )
                        incoming = data.get("roles", data)
                        self.editor.mutate(
                            "Import palette",
                            lambda d, incoming=incoming: d["roles"].update(
                                {k: v for k, v in incoming.items() if is_hex(v)}
                            ),
                        )
                    except (
                        OSError,
                        ValueError,
                        TypeError,
                        KeyError,
                        RuntimeError,
                        subprocess.SubprocessError,
                        curses.error,
                    ) as exc:
                        message(
                            stdscr,
                            "Import failed",
                            [str(exc)],
                            self.palette,
                            self.palette.error,
                        )
            elif key in (ord("o"), ord("O")):
                path = prompt(
                    stdscr,
                    "Export palette JSON",
                    str(Path.home() / f"{self.editor.theme_name}-palette.json"),
                    palette=self.palette,
                )
                if path:
                    try:
                        Path(path).expanduser().write_text(
                            json.dumps({"roles": resolved}, indent=2) + "\n",
                            encoding="utf-8",
                        )
                        self.status = f"Palette exported to {path}"
                    except OSError as exc:
                        message(
                            stdscr,
                            "Export failed",
                            [str(exc)],
                            self.palette,
                            self.palette.error,
                        )

    # ── wallpaper ──────────────────────────────────────────────────────
    def wallpaper_studio(self, stdscr: Any) -> None:
        path = prompt(stdscr, "Wallpaper path", "", palette=self.palette)
        if not path:
            return
        expanded = Path(path).expanduser()
        if not expanded.exists():
            message(
                stdscr,
                "File not found",
                [str(expanded)],
                self.palette,
                self.palette.error,
            )
            return
        try:
            colors = extract_wallpaper_palette(expanded, 8)
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
            curses.error,
        ) as exc:
            message(
                stdscr,
                "Palette extraction failed",
                [str(exc)],
                self.palette,
                self.palette.error,
            )
            return
        selected = 0
        dark = True
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr, "WALLPAPER STUDIO", "Dark" if dark else "Light", self.palette
            )
            draw_box(
                stdscr,
                3,
                2,
                height - 7,
                width - 4,
                "EXTRACTED PALETTE",
                self.palette.muted,
            )
            safe_addstr(stdscr, 5, 4, str(expanded), self.palette.muted, width - 8)
            row = 8
            for idx, color in enumerate(colors):
                attr = self.palette.selected if idx == selected else 0
                fill_line(stdscr, row + idx, 5, 28, " ", attr)
                safe_addstr(stdscr, row + idx, 5, f"{idx + 1}. {color}", attr, 28)
            preview_roles = generate_palette_from_seed(colors[selected], dark)
            temp = ensure_theme_schema(
                {"roles": preview_roles, "style": {}, "components": {}, "dark": dark}
            )
            for idx, line in enumerate(palette_preview(temp, 40)):
                safe_addstr(stdscr, 8 + idx, 38, line, 0, width - 42)
            draw_footer(
                stdscr,
                "↑↓ Seed color   D Toggle dark/light   Enter Create theme   Esc Cancel",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q")):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(colors) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key in (ord("d"), ord("D")):
                dark = not dark
            elif key in (10, 13):
                name = prompt(
                    stdscr,
                    "New theme name",
                    expanded.stem.replace(" ", "_"),
                    palette=self.palette,
                )
                if not name:
                    continue
                try:
                    roles = palette_from_wallpaper(expanded, dark)
                    data = ensure_theme_schema(
                        {
                            "name": name,
                            "dark": dark,
                            "roles": roles,
                            "style": {},
                            "components": {},
                            "wallpaper": str(expanded),
                        }
                    )
                    self.editor = ThemeEditor.from_data(
                        name,
                        data,
                        self.theme_dir,
                        self._preview_callback,
                        self._restore_callback,
                    )
                    self.current_name = safe_theme_name(name)
                    self.quick_style(stdscr)
                    return
                except (
                    OSError,
                    ValueError,
                    TypeError,
                    KeyError,
                    RuntimeError,
                    subprocess.SubprocessError,
                    curses.error,
                ) as exc:
                    message(
                        stdscr,
                        "Could not create theme",
                        [str(exc)],
                        self.palette,
                        self.palette.error,
                    )

    # ── shell style ──────────────────────────────────────────────────
    def shell_style_studio(self, stdscr: Any) -> None:
        names = theme_runtime.list_ui_styles()
        if not names:
            message(
                stdscr,
                "No UI styles",
                ["No UI styles found in the catalog."],
                self.palette,
                self.palette.error,
            )
            return
        active = theme_runtime.current_ui_style_name()
        selected = names.index(active) if active in names else 0
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr,
                "SHELL STYLE",
                f"Active: {theme_runtime.current_ui_style_name()}",
                self.palette,
            )
            split = max(24, min(36, width // 3))
            draw_box(stdscr, 3, 1, height - 6, split, "STYLES", self.palette.muted)
            labels = [
                f"{n} (custom)" if theme_runtime.is_custom_ui_style(n) else n
                for n in names
            ]
            draw_list(
                stdscr, 5, 3, height - 10, split - 4, labels, selected, self.palette
            )
            x = split + 3
            preview_w = max(20, width - x - 2)
            draw_box(
                stdscr,
                3,
                x,
                height - 6,
                preview_w,
                names[selected],
                self.palette.accent,
            )
            try:
                style = theme_runtime.load_ui_style(names[selected])
                row = 5
                safe_addstr(
                    stdscr,
                    row,
                    x + 2,
                    style.get("description", ""),
                    self.palette.muted,
                    preview_w - 4,
                )
                row += 2
                for key, value in sorted(style.get("patterns", {}).items()):
                    safe_addstr(stdscr, row, x + 2, f"{key}: {value}", 0, preview_w - 4)
                    row += 1
                    if row >= height - 8:
                        break
            except theme_runtime.UiStyleError as exc:
                safe_addstr(
                    stdscr, 5, x + 2, str(exc), self.palette.error, preview_w - 4
                )
            draw_footer(
                stdscr,
                "↑↓ Choose   Enter Edit live   Space Apply now   N New style   Esc Back",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q")):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(names) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key == ord(" "):
                try:
                    theme_runtime.apply_ui_style(names[selected])
                    self.status = f"Shell style: {names[selected]}"
                except theme_runtime.UiStyleError as exc:
                    self.status = f"Apply failed: {exc}"
            elif key in (10, 13):
                self._edit_ui_style(stdscr, names[selected])
                names = theme_runtime.list_ui_styles()
                if names and selected >= len(names):
                    selected = len(names) - 1
            elif key in (ord("n"), ord("N")):
                new_name = prompt(
                    stdscr,
                    "New style name",
                    f"{names[selected]}_custom",
                    palette=self.palette,
                )
                if not new_name:
                    continue
                try:
                    base = theme_runtime.load_ui_style(names[selected])
                    base["description"] = f"Custom style based on {names[selected]}"
                    theme_runtime.save_ui_style(new_name, base)
                except theme_runtime.UiStyleError as exc:
                    message(
                        stdscr,
                        "Could not create style",
                        [str(exc)],
                        self.palette,
                        self.palette.error,
                    )
                    continue
                names = theme_runtime.list_ui_styles()
                safe_new_name = safe_theme_name(new_name)
                selected = (
                    names.index(safe_new_name) if safe_new_name in names else selected
                )
                self._edit_ui_style(stdscr, safe_new_name)
                names = theme_runtime.list_ui_styles()

    def _edit_ui_style(self, stdscr: Any, name: str) -> None:
        previous_active = theme_runtime.current_ui_style_name()
        try:
            working = theme_runtime.load_ui_style(name)
        except theme_runtime.UiStyleError as exc:
            message(
                stdscr,
                "Could not open style",
                [str(exc)],
                self.palette,
                self.palette.error,
            )
            return
        metric_keys = sorted(working.get("metrics", {}).keys())
        pattern_keys = sorted(working.get("patterns", {}).keys())
        fields = [("metric", key) for key in metric_keys] + [
            ("pattern", key) for key in pattern_keys
        ]
        # Offer known values per pattern field to cycle through, gathered from
        # every installed style so custom vocabularies stay available too.
        pattern_choices: dict[str, list[str]] = {key: [] for key in pattern_keys}
        for other_name in theme_runtime.list_ui_styles():
            try:
                other = theme_runtime.load_ui_style(other_name)
            except theme_runtime.UiStyleError:
                continue
            for key in pattern_keys:
                value = other.get("patterns", {}).get(key)
                if isinstance(value, str) and value not in pattern_choices[key]:
                    pattern_choices[key].append(value)
        dirty = False
        selected = 0

        def push_preview() -> None:
            theme_runtime.preview_ui_style(working)

        push_preview()
        try:
            while True:
                stdscr.erase()
                height, width = stdscr.getmaxyx()
                is_custom = theme_runtime.is_custom_ui_style(name)
                subtitle = f"{'custom' if is_custom else 'bundled'} \u00b7 \u25cf LIVE"
                draw_header(
                    stdscr,
                    f"SHELL STYLE / {name.upper()}{' \u2022' if dirty else ''}",
                    subtitle,
                    self.palette,
                )
                draw_box(
                    stdscr, 3, 1, height - 7, width - 2, "FINE TUNE", self.palette.muted
                )
                start = max(0, selected - max(1, (height - 12) // 2))
                row = 5
                for idx in range(start, min(len(fields), start + height - 11)):
                    kind, key = fields[idx]
                    value = working[f"{kind}s"][key]
                    attr = self.palette.selected if idx == selected else 0
                    fill_line(stdscr, row, 3, width - 6, " ", attr)
                    safe_addstr(stdscr, row, 3, key, attr, max(20, (width - 6) // 2))
                    safe_addstr(
                        stdscr,
                        row,
                        3 + max(20, (width - 6) // 2),
                        str(value),
                        attr,
                        (width - 6) // 2 - 4,
                    )
                    row += 1
                self._draw_status(stdscr, height - 4)
                draw_footer(
                    stdscr,
                    "\u2191\u2193 Setting  \u2190\u2192 Adjust  Enter Exact/Cycle  S Save  Esc Back",
                    self.palette,
                )
                stdscr.refresh()
                key_code = stdscr.getch()
                if key_code in (27, ord("q")):
                    break
                if key_code in (curses.KEY_DOWN, ord("j")):
                    selected = min(len(fields) - 1, selected + 1)
                elif key_code in (curses.KEY_UP, ord("k")):
                    selected = max(0, selected - 1)
                elif fields and key_code in (
                    curses.KEY_LEFT,
                    ord("h"),
                    curses.KEY_RIGHT,
                    ord("l"),
                ):
                    kind, key = fields[selected]
                    direction = -1 if key_code in (curses.KEY_LEFT, ord("h")) else 1
                    if kind == "metric":
                        current = working["metrics"][key]
                        working["metrics"][key] = max(0, int(current) + direction)
                    else:
                        choices = pattern_choices.get(key) or [working["patterns"][key]]
                        idx = (
                            choices.index(working["patterns"][key])
                            if working["patterns"][key] in choices
                            else 0
                        )
                        working["patterns"][key] = choices[
                            (idx + direction) % len(choices)
                        ]
                    dirty = True
                    push_preview()
                elif fields and key_code in (10, 13):
                    kind, key = fields[selected]
                    if kind == "metric":
                        entered = prompt(
                            stdscr,
                            key,
                            str(working["metrics"][key]),
                            palette=self.palette,
                        )
                        if entered is not None:
                            try:
                                working["metrics"][key] = int(entered)
                                dirty = True
                                push_preview()
                            except ValueError:
                                self.status = f"'{entered}' is not a whole number"
                    else:
                        entered = prompt(
                            stdscr,
                            key,
                            str(working["patterns"][key]),
                            palette=self.palette,
                        )
                        if entered is not None and entered:
                            working["patterns"][key] = entered
                            dirty = True
                            push_preview()
                elif key_code in (ord("s"), ord("S")):
                    target_name = name
                    if not theme_runtime.is_custom_ui_style(name):
                        entered = prompt(
                            stdscr,
                            "Save as (bundled styles can't be overwritten)",
                            f"{name}_custom",
                            palette=self.palette,
                        )
                        if not entered:
                            continue
                        target_name = entered
                    try:
                        theme_runtime.save_ui_style(target_name, working)
                        theme_runtime.apply_ui_style(safe_theme_name(target_name))
                        self.status = f"Saved and applied shell style {safe_theme_name(target_name)}"
                        dirty = False
                        name = safe_theme_name(target_name)
                        previous_active = name
                    except (
                        OSError,
                        ValueError,
                        TypeError,
                        KeyError,
                        RuntimeError,
                        subprocess.SubprocessError,
                        curses.error,
                    ) as exc:
                        message(
                            stdscr,
                            "Save failed",
                            [str(exc)],
                            self.palette,
                            self.palette.error,
                        )
        finally:
            try:
                theme_runtime.restore_ui_style()
                if dirty:
                    self.status = (
                        f"Discarded shell style edits; restored {previous_active}"
                    )
            except theme_runtime.UiStyleError as exc:
                self.status = f"Could not restore shell style: {exc}"

    # ── theme manager ──────────────────────────────────────────────────
    def theme_manager(self, stdscr: Any) -> None:
        selected = 0
        while True:
            themes = list_themes(self.theme_dir)
            if not themes:
                message(stdscr, "No themes", ["No themes to manage."], self.palette)
                return
            selected = min(selected, len(themes) - 1)
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(stdscr, "MANAGE THEMES", f"{len(themes)} themes", self.palette)
            draw_box(
                stdscr,
                3,
                1,
                height - 7,
                min(38, width // 2),
                "THEMES",
                self.palette.muted,
            )
            draw_list(
                stdscr,
                5,
                3,
                height - 11,
                min(34, width // 2 - 4),
                themes,
                selected,
                self.palette,
            )
            x = min(41, width // 2 + 2)
            safe_addstr(
                stdscr, 5, x, themes[selected], self.palette.accent, width - x - 2
            )
            safe_addstr(stdscr, 7, x, "D Duplicate", 0, width - x - 2)
            safe_addstr(stdscr, 8, x, "R Rename", 0, width - x - 2)
            safe_addstr(stdscr, 9, x, "X Archive/Delete", 0, width - x - 2)
            safe_addstr(stdscr, 10, x, "C Compare with current", 0, width - x - 2)
            safe_addstr(stdscr, 11, x, "Enter Customize", 0, width - x - 2)
            draw_footer(
                stdscr,
                "↑↓ Theme  Enter Customize  D Duplicate  R Rename  X Archive  C Compare  Esc Back",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q")):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(themes) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key in (10, 13):
                if self._ensure_editor(stdscr, themes[selected]):
                    self.quick_style(stdscr)
            elif key in (ord("d"), ord("D")):
                name = prompt(
                    stdscr,
                    "Duplicate as",
                    themes[selected] + "_copy",
                    palette=self.palette,
                )
                if name:
                    try:
                        duplicate_theme(themes[selected], name, self.theme_dir)
                        self.status = f"Duplicated as {name}"
                    except (
                        OSError,
                        ValueError,
                        TypeError,
                        KeyError,
                        RuntimeError,
                        subprocess.SubprocessError,
                        curses.error,
                    ) as exc:
                        message(
                            stdscr,
                            "Duplicate failed",
                            [str(exc)],
                            self.palette,
                            self.palette.error,
                        )
            elif key in (ord("r"), ord("R")):
                name = prompt(
                    stdscr, "Rename theme", themes[selected], palette=self.palette
                )
                if name and name != themes[selected]:
                    try:
                        rename_theme(themes[selected], name, self.theme_dir)
                        if self.current_name == themes[selected]:
                            self.current_name = safe_theme_name(name)
                    except (
                        OSError,
                        ValueError,
                        TypeError,
                        KeyError,
                        RuntimeError,
                        subprocess.SubprocessError,
                        curses.error,
                    ) as exc:
                        message(
                            stdscr,
                            "Rename failed",
                            [str(exc)],
                            self.palette,
                            self.palette.error,
                        )
            elif key in (ord("x"), ord("X")):
                if themes[selected] == self.current_name:
                    message(
                        stdscr,
                        "Active theme",
                        ["Apply another theme before archiving this one."],
                        self.palette,
                        self.palette.warning,
                    )
                elif confirm(
                    stdscr,
                    "Archive theme",
                    f"Move {themes[selected]} to Theme Studio trash?",
                    self.palette,
                ):
                    delete_theme(themes[selected], self.theme_dir)
            elif key in (ord("c"), ord("C")):
                self.compare_themes(
                    stdscr, self.current_name or themes[selected], themes[selected]
                )

    def compare_themes(self, stdscr: Any, left_name: str, right_name: str) -> None:
        try:
            left, right = (
                load_theme(left_name, self.theme_dir),
                load_theme(right_name, self.theme_dir),
            )
        except (
            OSError,
            ValueError,
            TypeError,
            KeyError,
            RuntimeError,
            subprocess.SubprocessError,
            curses.error,
        ) as exc:
            message(
                stdscr, "Compare failed", [str(exc)], self.palette, self.palette.error
            )
            return
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr, "THEME COMPARISON", f"{left_name} ↔ {right_name}", self.palette
            )
            half = width // 2
            draw_box(stdscr, 3, 1, height - 6, half - 1, left_name, self.palette.muted)
            draw_box(
                stdscr,
                3,
                half,
                height - 6,
                width - half - 1,
                right_name,
                self.palette.muted,
            )
            for idx, line in enumerate(
                window_preview(left, half - 5, min(13, height - 10))
            ):
                safe_addstr(stdscr, 5 + idx, 3, line, 0, half - 5)
            for idx, line in enumerate(
                window_preview(right, width - half - 5, min(13, height - 10))
            ):
                safe_addstr(stdscr, 5 + idx, half + 2, line, 0, width - half - 5)
            draw_footer(stdscr, "Any key Back", self.palette)
            stdscr.refresh()
            stdscr.getch()
            return

    # ── advanced inspector ─────────────────────────────────────────────
    def advanced_inspector(self, stdscr: Any, jump_path: str | None = None) -> None:
        assert self.editor
        selected = 0
        while True:
            flat = self._flatten(self.editor.draft)
            paths = [path for path, _ in flat]
            if jump_path in paths:
                selected = paths.index(jump_path)
                jump_path = None
            selected = min(selected, max(0, len(flat) - 1))
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr, "ADVANCED INSPECTOR", self._status_right(), self.palette
            )
            left_w = min(56, max(34, width // 2))
            draw_box(stdscr, 3, 1, height - 7, left_w, "PROPERTY", self.palette.muted)
            start = max(0, selected - max(1, (height - 12) // 2))
            row = 5
            for idx in range(start, min(len(flat), start + height - 11)):
                path, value = flat[idx]
                attr = self.palette.selected if idx == selected else 0
                fill_line(stdscr, row, 3, left_w - 4, " ", attr)
                safe_addstr(stdscr, row, 3, path, attr, left_w - 22)
                safe_addstr(stdscr, row, left_w - 18, str(value), attr, 15)
                row += 1
            x = left_w + 3
            draw_box(
                stdscr,
                3,
                x,
                height - 7,
                width - x - 1,
                "VALUE / GENERATED EFFECT",
                self.palette.muted,
            )
            path, value = flat[selected]
            safe_addstr(stdscr, 5, x + 2, path, self.palette.accent, width - x - 5)
            safe_addstr(
                stdscr,
                7,
                x + 2,
                json.dumps(value, ensure_ascii=False),
                0,
                width - x - 5,
            )
            generated = self._generated_hint(path, value)
            for idx, line in enumerate(generated):
                safe_addstr(
                    stdscr, 10 + idx, x + 2, line, self.palette.muted, width - x - 5
                )
            draw_footer(
                stdscr,
                "↑↓ Property  Enter Edit  D Restore inherited  V View JSON  / Search  Esc Back",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if self._common_key(stdscr, key):
                continue
            if key in (27, ord("q")):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(flat) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key in (10, 13):
                entered = prompt(
                    stdscr,
                    path,
                    json.dumps(value) if not isinstance(value, str) else value,
                    palette=self.palette,
                )
                if entered is not None:
                    try:
                        parsed = json.loads(entered)
                    except json.JSONDecodeError:
                        parsed = entered
                    self.editor.mutate(
                        f"Edit {path}",
                        lambda d, path=path, parsed=parsed: deep_set(d, path, parsed),
                    )
            elif key in (ord("d"), ord("D")):
                original = deep_get(self.editor.original, path, None)
                self.editor.mutate(
                    f"Restore {path}",
                    lambda d, path=path, original=original: deep_set(
                        d, path, deepcopy(original)
                    ),
                )
            elif key in (ord("v"), ord("V")):
                text = json.dumps(
                    self.editor.draft, indent=2, ensure_ascii=False
                ).splitlines()
                self._scroll_text(stdscr, "THEME JSON", text)

    def _flatten(self, data: Any, prefix: str = "") -> list[tuple[str, Any]]:
        result: list[tuple[str, Any]] = []
        if isinstance(data, dict):
            for key in sorted(data):
                path = f"{prefix}.{key}" if prefix else key
                value = data[key]
                if isinstance(value, dict):
                    result.extend(self._flatten(value, path))
                elif isinstance(value, list):
                    result.append((path, value))
                else:
                    result.append((path, value))
        return result

    def _generated_hint(self, path: str, value: Any) -> list[str]:
        if path.endswith("active_border.angle"):
            return [f"Hyprland: col.active_border = rgba(...) rgba(...) {value}deg"]
        if path.endswith("border_width"):
            return [f"Hyprland / CSS border width: {value}px"]
        if path.startswith("components.waybar.modules"):
            return ["Waybar generated/config.jsonc", json.dumps(value)]
        if path.startswith("roles."):
            return [f"@define-color {path.split('.')[-1]} {value};"]
        return [
            "This value is inherited by its component renderer.",
            "Use D to restore the original/inherited value.",
        ]

    # ── search ─────────────────────────────────────────────────────────
    def search(self, stdscr: Any) -> None:
        query = prompt(stdscr, "Search settings", "", palette=self.palette)
        if query is None:
            return
        selected = 0
        while True:
            words = query.lower().split()
            results = [
                item
                for item in self.search_items
                if all(
                    word in (item["label"] + " " + item["path"]).lower()
                    for word in words
                )
            ]
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr, "SEARCH SETTINGS", f"{len(results)} results", self.palette
            )
            safe_addstr(stdscr, 3, 2, f"> {query}", self.palette.accent, width - 4)
            draw_list(
                stdscr,
                5,
                2,
                height - 9,
                width - 4,
                [r["label"] for r in results] or ["No matches"],
                selected,
                self.palette,
            )
            draw_footer(
                stdscr,
                "Type new search with /   ↑↓ Choose   Enter Open   Esc Close",
                self.palette,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q")):
                return
            if key == ord("/"):
                new = prompt(stdscr, "Search settings", query, palette=self.palette)
                if new is not None:
                    query = new
                    selected = 0
            elif key in (curses.KEY_DOWN, ord("j")) and results:
                selected = min(len(results) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")) and results:
                selected = max(0, selected - 1)
            elif key in (10, 13) and results:
                self._open_search_result(stdscr, results[selected])
                return

    def _open_search_result(self, stdscr: Any, item: dict[str, str]) -> None:
        if not self.editor and not self._ensure_editor(stdscr, self.current_name):
            return
        component = item["component"]
        path = item["path"]
        if component == "palette":
            self.palette_editor(stdscr, path)
        elif component == "quick":
            self.quick_style(stdscr)
        elif component == "waybar":
            self.waybar_editor(stdscr)
        elif component in COMPONENT_LABELS:
            self.component_editor(stdscr, component, path)
        else:
            self.advanced_inspector(stdscr, path)

    # ── save / validation ──────────────────────────────────────────────
    def save_dialog(self, stdscr: Any) -> None:
        assert self.editor
        name = self.editor.theme_name + "_custom"
        mode_new = True
        selected = 0
        while True:
            issues = self.editor.validate()
            errors, warnings = validation_summary(issues)
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            box_w = min(72, width - 4)
            box_h = min(20, height - 4)
            y, x = max(1, (height - box_h) // 2), max(2, (width - box_w) // 2)
            draw_box(stdscr, y, x, box_h, box_w, "SAVE THEME", self.palette.accent)
            labels = [
                f"Theme name: {name}",
                f"Save mode: {'Create a new theme' if mode_new else 'Replace current theme'}",
                "Include: Palette · Windows · Waybar · Apps · Wallpaper · Animation",
                f"Validation: {errors} errors · {warnings} suggestions",
                "Save & Apply",
                "Cancel",
            ]
            for idx, label in enumerate(labels):
                attr = self.palette.selected if idx == selected else 0
                fill_line(stdscr, y + 2 + idx * 2, x + 2, box_w - 4, " ", attr)
                safe_addstr(stdscr, y + 2 + idx * 2, x + 2, label, attr, box_w - 4)
            safe_addstr(
                stdscr,
                y + box_h - 2,
                x + 2,
                "↑↓ Choose · Enter edit/confirm · Esc cancel",
                self.palette.muted,
                box_w - 4,
            )
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q")):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(labels) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif (
                key in (curses.KEY_LEFT, curses.KEY_RIGHT, ord("h"), ord("l"))
                and selected == 1
            ):
                mode_new = not mode_new
            elif key in (10, 13):
                if selected == 0:
                    entered = prompt(stdscr, "Theme name", name, palette=self.palette)
                    if entered:
                        name = safe_theme_name(entered)
                elif selected == 1:
                    mode_new = not mode_new
                elif selected == 3:
                    lines = [
                        f"{i['level'].upper()} · {i['path']} · {i['message']}"
                        for i in issues
                    ] or ["No validation issues."]
                    self._scroll_text(stdscr, "VALIDATION REPORT", lines)
                elif selected == 4:
                    if errors:
                        message(
                            stdscr,
                            "Cannot save yet",
                            [f"Fix {errors} validation error(s) first."],
                            self.palette,
                            self.palette.error,
                        )
                        continue
                    target = name if mode_new else self.editor.theme_name
                    try:
                        self.editor.save(target, replace=not mode_new, apply=False)
                        theme_runtime.apply_saved_theme(target)
                        self.current_name = target
                        self.original_active = target
                        self.editor.desktop_preview = False
                        self.status = f"Saved and applied {target}"
                        return
                    except (
                        OSError,
                        ValueError,
                        TypeError,
                        KeyError,
                        RuntimeError,
                        subprocess.SubprocessError,
                        curses.error,
                    ) as exc:
                        message(
                            stdscr,
                            "Save failed",
                            [str(exc)],
                            self.palette,
                            self.palette.error,
                        )
                elif selected == 5:
                    return

    # ── misc dialogs ───────────────────────────────────────────────────
    def help(self, stdscr: Any) -> None:
        lines = [
            "Theme Studio is layered so beginners never face a wall of settings.",
            "",
            "Home → Quick Style → Component rooms → Advanced Inspector",
            "",
            "Arrows       Navigate or adjust",
            "Enter        Open, edit, or confirm",
            "Space        Toggle temporary desktop preview",
            "Tab          Switch simple/detail views or panes",
            "/            Search every setting",
            "U            Undo",
            "Ctrl+R       Redo",
            "S            Save",
            "P            Presets",
            "R            Reset current room",
            "Esc          Back",
            "",
            "Mock previews are instant and safe. Live preview is temporary and",
            "automatically returns to the previous theme when cancelled.",
        ]
        self._scroll_text(stdscr, "HELP", lines)

    def _simple_picker(self, stdscr: Any, title: str, items: list[str]) -> int | None:
        selected = 0
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(stdscr, title, "", self.palette)
            draw_list(
                stdscr, 4, 3, height - 8, width - 6, items, selected, self.palette
            )
            draw_footer(stdscr, "↑↓ Choose  Enter Select  Esc Cancel", self.palette)
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q")):
                return None
            if key in (curses.KEY_DOWN, ord("j")):
                selected = min(len(items) - 1, selected + 1)
            elif key in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif key in (10, 13):
                return selected

    def _scroll_text(self, stdscr: Any, title: str, lines: list[str]) -> None:
        offset = 0
        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            draw_header(
                stdscr,
                title,
                f"{offset + 1}-{min(len(lines), offset + height - 5)} / {len(lines)}",
                self.palette,
            )
            for idx, line in enumerate(lines[offset : offset + height - 5]):
                safe_addstr(stdscr, 3 + idx, 2, line, 0, width - 4)
            draw_footer(stdscr, "↑↓ Scroll  PgUp/PgDn  Esc Back", self.palette)
            stdscr.refresh()
            key = stdscr.getch()
            if key in (27, ord("q"), 10, 13):
                return
            if key in (curses.KEY_DOWN, ord("j")):
                offset = min(max(0, len(lines) - 1), offset + 1)
            elif key in (curses.KEY_UP, ord("k")):
                offset = max(0, offset - 1)
            elif key == curses.KEY_NPAGE:
                offset = min(max(0, len(lines) - 1), offset + height - 6)
            elif key == curses.KEY_PPAGE:
                offset = max(0, offset - height + 6)


def launch(theme_dir: str | os.PathLike[str] | None = None) -> None:
    app = ThemeStudio(Path(theme_dir).expanduser() if theme_dir else None)
    curses.wrapper(app.run)


if __name__ == "__main__":
    launch()
