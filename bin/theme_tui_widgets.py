"""Small curses widgets used by Theme Studio."""

from __future__ import annotations

import curses
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass
class Palette:
    normal: int = 0
    accent: int = 0
    selected: int = 0
    muted: int = 0
    success: int = 0
    warning: int = 0
    error: int = 0
    panel: int = 0


def init_palette() -> Palette:
    if not curses.has_colors():
        return Palette()
    curses.start_color()
    curses.use_default_colors()
    pairs = [
        (1, curses.COLOR_CYAN, -1),
        (2, curses.COLOR_BLACK, curses.COLOR_CYAN),
        (3, curses.COLOR_WHITE, -1),
        (4, curses.COLOR_GREEN, -1),
        (5, curses.COLOR_YELLOW, -1),
        (6, curses.COLOR_RED, -1),
        (7, curses.COLOR_MAGENTA, -1),
    ]
    for pair, fg, bg in pairs:
        try:
            curses.init_pair(pair, fg, bg)
        except curses.error:
            pass
    return Palette(
        normal=curses.color_pair(3),
        accent=curses.color_pair(1) | curses.A_BOLD,
        selected=curses.color_pair(2) | curses.A_BOLD,
        muted=curses.A_DIM,
        success=curses.color_pair(4),
        warning=curses.color_pair(5),
        error=curses.color_pair(6),
        panel=curses.color_pair(7) | curses.A_BOLD,
    )


def safe_addstr(
    win: Any, y: int, x: int, text: str, attr: int = 0, width: int | None = None
) -> None:
    try:
        h, w = win.getmaxyx()
        if y < 0 or y >= h or x < 0 or x >= w:
            return
        room = max(0, w - x - 1)
        if width is not None:
            room = min(room, max(0, width))
        win.addnstr(y, x, str(text), room, attr)
    except curses.error:
        pass


def fill_line(
    win: Any, y: int, x: int, width: int, char: str = " ", attr: int = 0
) -> None:
    safe_addstr(win, y, x, char * max(0, width), attr, width)


def draw_box(
    win: Any, y: int, x: int, height: int, width: int, title: str = "", attr: int = 0
) -> None:
    if height < 2 or width < 4:
        return
    safe_addstr(win, y, x, "╭" + "─" * (width - 2) + "╮", attr, width)
    for row in range(1, height - 1):
        safe_addstr(win, y + row, x, "│", attr)
        safe_addstr(win, y + row, x + width - 1, "│", attr)
    safe_addstr(win, y + height - 1, x, "╰" + "─" * (width - 2) + "╯", attr, width)
    if title:
        label = f" {title} "
        safe_addstr(win, y, x + 2, label, attr | curses.A_BOLD, width - 4)


def draw_header(win: Any, title: str, right: str, palette: Palette) -> None:
    _, width = win.getmaxyx()
    fill_line(win, 0, 0, width - 1, " ", palette.panel)
    safe_addstr(win, 0, 1, f"✦ {title}", palette.panel, max(0, width - len(right) - 5))
    if right:
        safe_addstr(win, 0, max(1, width - len(right) - 2), right, palette.panel)
    safe_addstr(win, 1, 0, "─" * max(0, width - 1), palette.muted)


def draw_footer(win: Any, text: str, palette: Palette) -> None:
    height, width = win.getmaxyx()
    safe_addstr(win, height - 2, 0, "─" * max(0, width - 1), palette.muted)
    fill_line(win, height - 1, 0, width - 1, " ")
    safe_addstr(win, height - 1, 1, text, palette.muted, width - 3)


def draw_list(
    win: Any,
    y: int,
    x: int,
    height: int,
    width: int,
    items: Iterable[str],
    selected: int,
    palette: Palette,
    offset: int | None = None,
    markers: dict[int, str] | None = None,
) -> int:
    values = list(items)
    if not values:
        safe_addstr(win, y, x, "(none)", palette.muted, width)
        return 0
    visible = max(1, height)
    if offset is None:
        offset = max(0, min(selected - visible // 2, max(0, len(values) - visible)))
    for row, index in enumerate(range(offset, min(len(values), offset + visible))):
        marker = (markers or {}).get(index, "")
        text = f"{marker}{values[index]}"
        attr = palette.selected if index == selected else 0
        fill_line(win, y + row, x, width, " ", attr)
        safe_addstr(win, y + row, x, text, attr, width)
    return offset


def slider_text(
    value: float,
    minimum: float,
    maximum: float,
    width: int = 16,
    precision: int | None = None,
) -> str:
    if maximum <= minimum:
        ratio = 0.0
    else:
        ratio = (float(value) - minimum) / (maximum - minimum)
    ratio = max(0.0, min(1.0, ratio))
    knob = round(ratio * max(1, width - 1))
    bar = "━" * knob + "●" + "━" * max(0, width - knob - 1)
    if precision is None:
        precision = (
            2 if isinstance(value, float) and not float(value).is_integer() else 0
        )
    return f"{bar} {value:.{precision}f}"


def role_swatch(value: str, width: int = 10) -> str:
    return f"{value:<{width}}"


def prompt(
    stdscr: Any,
    title: str,
    initial: str = "",
    max_length: int = 120,
    palette: Palette | None = None,
) -> str | None:
    palette = palette or Palette()
    height, width = stdscr.getmaxyx()
    box_w = min(max(34, len(title) + 8), max(34, width - 4))
    box_h = 7
    y = max(1, (height - box_h) // 2)
    x = max(1, (width - box_w) // 2)
    draw_box(stdscr, y, x, box_h, box_w, title, palette.accent)
    value = list(initial[:max_length])
    cursor = len(value)
    curses.curs_set(1)
    while True:
        fill_line(stdscr, y + 3, x + 2, box_w - 4)
        shown = "".join(value)
        start = max(0, cursor - (box_w - 8))
        safe_addstr(stdscr, y + 3, x + 2, shown[start:], 0, box_w - 4)
        safe_addstr(
            stdscr, y + 5, x + 2, "Enter confirm · Esc cancel", palette.muted, box_w - 4
        )
        try:
            stdscr.move(y + 3, x + 2 + min(cursor - start, box_w - 5))
        except curses.error:
            pass
        stdscr.refresh()
        key = stdscr.get_wch()
        if key in ("\n", "\r"):
            curses.curs_set(0)
            return "".join(value)
        if key == "\x1b":
            curses.curs_set(0)
            return None
        if key in (curses.KEY_BACKSPACE, "\b", "\x7f"):
            if cursor > 0:
                cursor -= 1
                value.pop(cursor)
        elif key == curses.KEY_DC:
            if cursor < len(value):
                value.pop(cursor)
        elif key == curses.KEY_LEFT:
            cursor = max(0, cursor - 1)
        elif key == curses.KEY_RIGHT:
            cursor = min(len(value), cursor + 1)
        elif key == curses.KEY_HOME:
            cursor = 0
        elif key == curses.KEY_END:
            cursor = len(value)
        elif isinstance(key, str) and key.isprintable() and len(value) < max_length:
            value.insert(cursor, key)
            cursor += 1


def confirm(
    stdscr: Any,
    title: str,
    message: str,
    palette: Palette | None = None,
    default: bool = False,
) -> bool:
    palette = palette or Palette()
    height, width = stdscr.getmaxyx()
    box_w = min(max(42, len(message) + 6), max(42, width - 4))
    box_h = 8
    y = max(1, (height - box_h) // 2)
    x = max(1, (width - box_w) // 2)
    draw_box(stdscr, y, x, box_h, box_w, title, palette.warning)
    safe_addstr(stdscr, y + 2, x + 2, message, 0, box_w - 4)
    choice = 0 if default else 1
    while True:
        labels = [" Yes ", " No "]
        total = sum(map(len, labels)) + 4
        start = x + max(2, (box_w - total) // 2)
        for idx, label in enumerate(labels):
            attr = palette.selected if idx == choice else 0
            safe_addstr(stdscr, y + 5, start, label, attr)
            start += len(label) + 4
        stdscr.refresh()
        key = stdscr.getch()
        if key in (curses.KEY_LEFT, curses.KEY_RIGHT, ord("h"), ord("l"), 9):
            choice = 1 - choice
        elif key in (10, 13):
            return choice == 0
        elif key in (27, ord("q")):
            return False
        elif key in (ord("y"), ord("Y")):
            return True
        elif key in (ord("n"), ord("N")):
            return False


def message(
    stdscr: Any,
    title: str,
    lines: Iterable[str],
    palette: Palette | None = None,
    attr: int = 0,
) -> None:
    palette = palette or Palette()
    values = list(lines)
    height, width = stdscr.getmaxyx()
    box_w = min(
        max(46, max((len(line) for line in values), default=0) + 6), max(46, width - 4)
    )
    box_h = min(max(7, len(values) + 5), max(7, height - 2))
    y = max(1, (height - box_h) // 2)
    x = max(1, (width - box_w) // 2)
    draw_box(stdscr, y, x, box_h, box_w, title, palette.accent)
    for index, line in enumerate(values[: box_h - 4]):
        safe_addstr(stdscr, y + 2 + index, x + 2, line, attr, box_w - 4)
    safe_addstr(stdscr, y + box_h - 2, x + 2, "Press any key", palette.muted, box_w - 4)
    stdscr.refresh()
    stdscr.getch()
