"""Mock preview renderers used by the curses Theme Studio."""

from __future__ import annotations

from typing import Any

from theme_schema import deep_get, resolve_roles


def _fit(text: str, width: int) -> str:
    if width <= 0:
        return ""
    return text if len(text) <= width else text[: max(0, width - 1)] + "…"


def _box(width: int, height: int, title: str = "") -> list[str]:
    width = max(8, width)
    height = max(3, height)
    top = "╭" + "─" * (width - 2) + "╮"
    if title and width > len(title) + 6:
        label = f" {title} "
        top = "╭" + label + "─" * (width - len(label) - 2) + "╮"
    lines = [top]
    lines.extend("│" + " " * (width - 2) + "│" for _ in range(height - 2))
    lines.append("╰" + "─" * (width - 2) + "╯")
    return lines


def window_preview(
    theme: dict[str, Any], width: int = 34, height: int = 12
) -> list[str]:
    win = deep_get(theme, "components.windows", {})
    active = _box(width, max(7, height - 3), "ACTIVE WINDOW")
    radius = int(win.get("corner_radius", 10))
    border = int(win.get("border_width", 2))
    blur = win.get("blur", {})
    shadow = win.get("shadow", {})
    content = [
        f" gaps {win.get('gaps_in', 5)}/{win.get('gaps_out', 10)}  border {border}px",
        f" corners {radius}px  opacity {float(win.get('active_opacity', 1.0)):.2f}",
        f" blur {'on' if blur.get('enabled', True) else 'off'} · {blur.get('size', 8)} × {blur.get('passes', 3)}",
        f" shadow {'on' if shadow.get('enabled', True) else 'off'} · {shadow.get('radius', 20)}px",
    ]
    for idx, text in enumerate(content, 1):
        if idx < len(active) - 1:
            active[idx] = "│" + _fit(text, width - 2).ljust(width - 2) + "│"
    inactive_w = max(16, width - 7)
    inactive = _box(inactive_w, 3, "INACTIVE")
    inactive[1] = (
        "│"
        + _fit(
            f" opacity {float(win.get('inactive_opacity', 0.92)):.2f} · dim {float(win.get('inactive_dim', 0.08)):.2f}",
            inactive_w - 2,
        ).ljust(inactive_w - 2)
        + "│"
    )
    return active + [" " * 3 + line for line in inactive]


def waybar_preview(theme: dict[str, Any], width: int = 54) -> list[str]:
    bar = deep_get(theme, "components.waybar", {})
    layout = str(bar.get("layout", "islands"))
    modules = bar.get("modules", {})
    left = modules.get("left", [])
    center = modules.get("center", [])
    right = modules.get("right", [])

    def short(module: str) -> str:
        names = {
            "clock": "12:42",
            "network": "",
            "pulseaudio": "󰕾",
            "battery": "󰁹",
            "tray": "•••",
            "custom/window-tracker": "themes",
            "hyprland/window": "themes",
            "custom/vpn": "󰖂",
            "custom/sysstat": "CPU 12%",
            "custom/notifications": "",
            "custom/running-apps": "Apps",
            "custom/launcher": "󰀻",
        }
        if module.startswith("custom/ws"):
            return module.removeprefix("custom/ws")
        return names.get(module, module.split("/")[-1][:8])

    def group(items: list[str]) -> str:
        return " ".join(short(m) for m in items)

    l, c, r = group(left), group(center), group(right)
    if layout == "full":
        inside = f" {l}"
        remaining = width - len(inside) - len(r) - 2
        inside += c.center(max(1, remaining)) + r + " "
        return [
            "┌" + "─" * max(1, width - 2) + "┐",
            "│" + _fit(inside, width - 2).ljust(width - 2) + "│",
            "└" + "─" * max(1, width - 2) + "┘",
        ]
    if layout == "minimal":
        text = f"{l}     {c}     {r}"
        return [_fit(text.center(width), width)]
    left_box = f"╭ {l} ╮" if l else ""
    center_box = f"╭ {c} ╮" if c else ""
    right_box = f"╭ {r} ╮" if r else ""
    gap = max(1, width - len(left_box) - len(center_box) - len(right_box))
    first = (
        left_box + " " * (gap // 2) + center_box + " " * (gap - gap // 2) + right_box
    )
    return [_fit(first, width)]


def launcher_preview(
    theme: dict[str, Any], width: int = 36, height: int = 11
) -> list[str]:
    launcher = deep_get(theme, "components.launcher", {})
    lines = _box(width, height, str(launcher.get("provider", "wofi")).upper())
    rows = [
        "Search applications…",
        "󰆍  Terminal",
        "󰈹  Browser",
        "󰉋  Files",
        "󰏘  Settings",
    ]
    for idx, row in enumerate(rows, 1):
        if idx >= len(lines) - 1:
            break
        marker = "› " if idx == 2 else "  "
        lines[idx] = "│" + _fit(marker + row, width - 2).ljust(width - 2) + "│"
    return lines


def notification_preview(theme: dict[str, Any], width: int = 36) -> list[str]:
    notify = deep_get(theme, "components.notifications", {})
    lines = _box(width, 7, "NOTIFICATION")
    payload = [
        "Theme Studio",
        "Your desktop preview is ready.",
        f"{notify.get('origin', 'top-right')} · {notify.get('width', 340)}px",
        f"radius {notify.get('radius', 10)} · padding {notify.get('padding', 12)}",
    ]
    for idx, row in enumerate(payload, 1):
        lines[idx] = "│" + _fit(" " + row, width - 2).ljust(width - 2) + "│"
    return lines


def palette_preview(theme: dict[str, Any], width: int = 44) -> list[str]:
    roles = resolve_roles(theme.get("roles", {}))
    names = [
        "bg",
        "bg_alt",
        "text",
        "text_dim",
        "accent",
        "accent2",
        "urgent",
        "success",
    ]
    lines = ["PALETTE"]
    for role in names:
        lines.append(f"{role:<14} {roles.get(role, '#000000')}")
    return [_fit(line, width) for line in lines]


def component_preview(
    theme: dict[str, Any], component: str, width: int = 40, height: int = 14
) -> list[str]:
    if component == "windows":
        return window_preview(theme, width, height)
    if component == "waybar":
        return waybar_preview(theme, width)
    if component == "launcher":
        return launcher_preview(theme, width, height)
    if component == "notifications":
        return notification_preview(theme, width)
    if component == "palette":
        return palette_preview(theme, width)
    box = _box(width, max(7, height), component.replace("_", " ").upper())
    data = deep_get(theme, f"components.{component}", {})
    for idx, (key, value) in enumerate(data.items(), 1):
        if idx >= len(box) - 1:
            break
        if isinstance(value, dict):
            value = "{…}"
        box[idx] = (
            "│"
            + _fit(f" {key.replace('_', ' ')}: {value}", width - 2).ljust(width - 2)
            + "│"
        )
    return box
