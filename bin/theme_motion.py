from __future__ import annotations

import json
from typing import Any

WORKSPACE_STYLES = {
    "slide": "slide",
    "slidevert": "slidevert",
    "fade": "",
    "slidefade": "slidefade 50%",
    "slidefadevert": "slidefadevert 40%",
}

EFFECT_PROFILES = {
    "performance": {
        "components.windows.blur.enabled": False,
        "components.windows.blur.size": 3,
        "components.windows.blur.passes": 1,
        "components.windows.shadow.enabled": True,
        "components.windows.shadow.radius": 8,
        "components.windows.inactive_dim": 0.0,
        "components.windows.glow": 0,
        "style.animation_preset": "spring",
        "style.spring_stiffness": 360.0,
        "style.spring_dampening": 32.0,
        "style.workspace_style": "slidefade",
        "style.motion_blur_mode": "disabled",
        "style.wobble_mode": "disabled",
    },
    "balanced": {
        "components.windows.blur.enabled": True,
        "components.windows.blur.size": 5,
        "components.windows.blur.passes": 1,
        "components.windows.shadow.enabled": True,
        "components.windows.shadow.radius": 18,
        "components.windows.inactive_dim": 0.035,
        "components.windows.glow": 9,
        "style.animation_preset": "spring",
        "style.spring_stiffness": 285.0,
        "style.spring_dampening": 25.0,
        "style.workspace_style": "slidefade",
        "style.motion_blur_mode": "enabled",
        "style.motion_blur_samples": 3,
        "style.wobble_mode": "disabled",
    },
    "cinematic": {
        "components.windows.blur.enabled": True,
        "components.windows.blur.size": 7,
        "components.windows.blur.passes": 2,
        "components.windows.shadow.enabled": True,
        "components.windows.shadow.radius": 28,
        "components.windows.inactive_dim": 0.055,
        "components.windows.glow": 13,
        "style.animation_preset": "spring",
        "style.spring_stiffness": 245.0,
        "style.spring_dampening": 22.0,
        "style.workspace_style": "slidefade",
        "style.motion_blur_mode": "enabled",
        "style.motion_blur_samples": 4,
    },
}


def animation_lines(
    name: str, style: dict[str, Any], preset_lines: list[str]
) -> tuple[bool, list[str]]:
    if name == "none":
        return False, []
    if name in {"custom", "spring"}:
        x1 = float(style.get("custom_bezier_x1", 0.16))
        y1 = float(style.get("custom_bezier_y1", 1.0))
        x2 = float(style.get("custom_bezier_x2", 0.3))
        y2 = float(style.get("custom_bezier_y2", 1.0))
        lines = [
            f"bezier = studioCustom, {x1}, {y1}, {x2}, {y2}",
            "animation = windowsIn, 1, 6, studioCustom, slide",
            "animation = windowsOut, 1, 5, studioCustom, slide",
            "animation = windowsMove, 1, 5, studioCustom",
            "animation = fade, 1, 5, studioCustom",
            "animation = fadeDim, 1, 5, studioCustom",
            "animation = workspaces, 1, 6, studioCustom, slide",
            "animation = border, 1, 6, studioCustom",
        ]
    else:
        lines = list(preset_lines)

    duration = max(0.25, min(3.0, float(style.get("animation_speed_multiplier", 1.0))))
    workspace = str(style.get("workspace_style", "preset"))
    result: list[str] = []
    for line in lines:
        if not line.startswith("animation ="):
            result.append(line)
            continue
        parts = [part.strip() for part in line.split("=", 1)[1].split(",")]
        parts[2] = str(max(1, round(float(parts[2]) * duration)))
        if (
            parts[0] in {"workspaces", "specialWorkspace"}
            and workspace in WORKSPACE_STYLES
        ):
            parts = parts[:4]
            if WORKSPACE_STYLES[workspace]:
                parts.append(WORKSPACE_STYLES[workspace])
        result.append("animation = " + ", ".join(parts))

    configured = {
        line.split("=", 1)[1].split(",", 1)[0].strip()
        for line in result
        if line.startswith("animation =")
    }
    curves = [
        line.split("=", 1)[1].split(",", 1)[0].strip()
        for line in result
        if line.startswith("bezier =")
    ]
    curve = curves[0] if curves else "default"
    speed = max(1, round(5 * duration))
    for leaf in (
        "specialWorkspace",
        "fadePopups",
        "fadeSwitch",
        "fadeShadow",
        "fadeGlow",
        "fadeDim",
        "borderangle",
    ):
        if leaf not in configured:
            transition = (
                WORKSPACE_STYLES.get(workspace, "")
                if leaf == "specialWorkspace"
                else ""
            )
            suffix = f", {transition}" if transition else ""
            result.append(f"animation = {leaf}, 1, {speed}, {curve}{suffix}")

    layer_enabled = bool(style.get("layer_animation_enabled", True))
    layer_style = str(style.get("layer_style", "fade"))
    if layer_style not in {"fade", "slide"}:
        layer_style = "fade"
    layer_speed = max(1, round(6 * duration))
    for leaf in ("layers", "layersIn", "layersOut"):
        result.append(
            f"animation = {leaf}, {int(layer_enabled)}, {layer_speed}, default, {layer_style}"
        )
    return True, result


def render_lua(name: str, style: dict[str, Any], preset_lines: list[str]) -> list[str]:
    enabled, animations = animation_lines(name, style, preset_lines)
    lines = [f"hl.config({{ animations = {{ enabled = {str(enabled).lower()} }} }})"]
    for line in animations:
        key, value = line.split("=", 1)
        parts = [part.strip() for part in value.split(",")]
        if key.strip() == "bezier":
            curve, x1, y1, x2, y2 = parts
            if name == "spring" and curve == "studioCustom":
                mass = max(0.2, min(3.0, float(style.get("spring_mass", 1.0))))
                stiffness = max(
                    50.0, min(600.0, float(style.get("spring_stiffness", 245.0)))
                )
                dampening = max(
                    5.0, min(60.0, float(style.get("spring_dampening", 22.0)))
                )
                lines.append(
                    f'hl.curve("studioCustom", {{ type = "spring", mass = {mass}, '
                    f"stiffness = {stiffness}, dampening = {dampening} }})"
                )
                continue
            lines.append(
                f'hl.curve({json.dumps(curve)}, {{ type = "bezier", '
                f"points = {{ {{ {x1}, {y1} }}, {{ {x2}, {y2} }} }} }})"
            )
        else:
            leaf, onoff, speed, curve = parts[:4]
            extra = f", style = {json.dumps(parts[4])}" if len(parts) > 4 else ""
            curve_type = (
                "spring" if name == "spring" and curve == "studioCustom" else "bezier"
            )
            lines.append(
                f"hl.animation({{ leaf = {json.dumps(leaf)}, enabled = "
                f"{str(onoff == '1').lower()}, speed = {speed}, "
                f"{curve_type} = {json.dumps(curve)}{extra} }})"
            )
    return lines


def render_effects_lua(style: dict[str, Any]) -> list[str]:
    blur = str(style.get("motion_blur_mode", "inherit"))
    wobble = str(style.get("wobble_mode", "inherit"))
    if blur == "inherit" and wobble == "inherit":
        return []
    lines = [
        'local studio_version_pipe = io.popen("Hyprland --version 2>/dev/null")',
        'local studio_version = studio_version_pipe and studio_version_pipe:read("*a") or ""',
        "if studio_version_pipe then studio_version_pipe:close() end",
        'local studio_major, studio_minor = studio_version:match("[vV]?(%d+)%.(%d+)")',
        "studio_major, studio_minor = tonumber(studio_major) or 0, tonumber(studio_minor) or 0",
    ]
    if blur in {"enabled", "disabled"}:
        samples = max(1, min(10, int(style.get("motion_blur_samples", 4))))
        lines.extend(
            [
                "if studio_major > 0 or studio_minor >= 56 then",
                f"    hl.config({{ decoration = {{ motion_blur = {{ enabled = {str(blur == 'enabled').lower()}, samples = {samples} }} }} }})",
                "end",
            ]
        )
    if wobble in {"enabled", "disabled"}:
        intensity = max(0.0, min(0.2, float(style.get("wobble_intensity", 0.035))))
        stiffness = max(50, min(800, int(style.get("wobble_stiffness", 430))))
        damping = max(1, min(100, int(style.get("wobble_damping", 35))))
        mass = max(0.1, min(4.0, float(style.get("wobble_mass", 1.0))))
        lines.extend(
            [
                "if studio_major > 0 or studio_minor >= 57 then",
                (
                    "    hl.config({ decoration = { wobble = { "
                    f"enabled = {str(wobble == 'enabled').lower()}, intensity = {intensity}, "
                    f"stiffness = {stiffness}, damping = {damping}, mass = {mass} "
                    "} } })"
                ),
                "end",
            ]
        )
    return lines
