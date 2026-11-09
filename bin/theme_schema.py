"""Schema, presets, validation, search metadata, and palette helpers for Theme Studio.

The module intentionally has no third-party dependency. Pillow is used only when
available for wallpaper palette extraction.
"""

from __future__ import annotations

import colorsys
import json
import math
import os
import re
from collections.abc import Iterable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
CORE_ROLES = (
    "bg",
    "bg_alt",
    "text",
    "text_dim",
    "accent",
    "accent2",
    "urgent",
    "focus",
    "border_normal",
)
SEMANTIC_ROLES = (
    "surface_0",
    "surface_1",
    "surface_2",
    "overlay",
    "hover",
    "selected",
    "border_subtle",
    "border_strong",
    "success",
    "warning",
    "info",
    "disabled",
    "shadow",
    "on_accent",
    "on_urgent",
)
ALL_ROLES = CORE_ROLES + SEMANTIC_ROLES

ROLE_LABELS = {
    "bg": "Main background",
    "bg_alt": "Raised surface",
    "text": "Main text",
    "text_dim": "Muted text",
    "accent": "Accent",
    "accent2": "Accent 2",
    "urgent": "Urgent / error",
    "focus": "Focus color",
    "border_normal": "Inactive border",
    "surface_0": "Base surface",
    "surface_1": "Raised surface 1",
    "surface_2": "Raised surface 2",
    "overlay": "Overlay",
    "hover": "Hover",
    "selected": "Selection",
    "border_subtle": "Subtle border",
    "border_strong": "Strong border",
    "success": "Success",
    "warning": "Warning",
    "info": "Information",
    "disabled": "Disabled",
    "shadow": "Shadow",
    "on_accent": "Text on accent",
    "on_urgent": "Text on urgent",
}

DEFAULT_WAYBAR_MODULES = {
    "left": [
        "custom/ws1",
        "custom/ws2",
        "custom/ws3",
        "custom/ws4",
        "custom/ws5",
        "custom/ws6",
        "custom/ws7",
        "custom/ws8",
        "custom/ws9",
        "custom/ws10",
        "custom/window-tracker",
    ],
    "center": ["clock"],
    "right": [
        "custom/vpn",
        "custom/sysstat",
        "pulseaudio",
        "network",
        "custom/notifications",
        "custom/running-apps",
        "tray",
    ],
}

SPACING_PRESETS = {
    "compact": {
        "style.gaps": 6,
        "components.windows.gaps_in": 3,
        "components.windows.gaps_out": 6,
        "components.waybar.module_gap": 3,
        "components.waybar.module_padding": 6,
        "components.launcher.padding": 7,
        "components.notifications.padding": 8,
    },
    "cozy": {
        "style.gaps": 10,
        "components.windows.gaps_in": 5,
        "components.windows.gaps_out": 10,
        "components.waybar.module_gap": 6,
        "components.waybar.module_padding": 10,
        "components.launcher.padding": 10,
        "components.notifications.padding": 12,
    },
    "airy": {
        "style.gaps": 18,
        "components.windows.gaps_in": 9,
        "components.windows.gaps_out": 18,
        "components.waybar.module_gap": 10,
        "components.waybar.module_padding": 14,
        "components.launcher.padding": 16,
        "components.notifications.padding": 18,
    },
}

DENSITY_PRESETS = {
    "compact": {
        "components.waybar.height": 28,
        "components.waybar.font_size": 11,
        "components.waybar.icon_size": 14,
        "components.notifications.width": 300,
    },
    "comfortable": {
        "components.waybar.height": 34,
        "components.waybar.font_size": 13,
        "components.waybar.icon_size": 18,
        "components.notifications.width": 340,
    },
    "spacious": {
        "components.waybar.height": 42,
        "components.waybar.font_size": 15,
        "components.waybar.icon_size": 21,
        "components.notifications.width": 400,
    },
}

SHAPE_PRESETS = {
    "sharp": {
        "components.windows.corner_radius": 0,
        "components.windows.rounding_power": 2.0,
        "components.waybar.radius": 0,
    },
    "soft": {
        "components.windows.corner_radius": 10,
        "components.windows.rounding_power": 2.0,
        "components.waybar.radius": 10,
    },
    "rounded": {
        "components.windows.corner_radius": 16,
        "components.windows.rounding_power": 2.5,
        "components.waybar.radius": 14,
    },
    "pillowy": {
        "components.windows.corner_radius": 24,
        "components.windows.rounding_power": 3.0,
        "components.waybar.radius": 18,
    },
    "retro_box": {
        "components.windows.corner_radius": 2,
        "components.windows.rounding_power": 2.0,
        "components.waybar.radius": 2,
        "components.windows.border_width": 2,
    },
}

TEXTURE_PRESETS = {
    "clear": {
        "components.windows.blur.enabled": False,
        "components.windows.active_opacity": 1.0,
        "components.windows.inactive_opacity": 1.0,
        "components.waybar.opacity": 1.0,
    },
    "frosted": {
        "components.windows.blur.enabled": True,
        "components.windows.blur.size": 8,
        "components.windows.blur.passes": 3,
        "components.windows.active_opacity": 0.96,
        "components.windows.inactive_opacity": 0.90,
        "components.waybar.blur": True,
        "components.waybar.opacity": 0.82,
    },
    "haze": {
        "components.windows.blur.enabled": True,
        "components.windows.blur.size": 12,
        "components.windows.blur.passes": 4,
        "components.windows.blur.noise": 0.02,
        "components.windows.active_opacity": 0.91,
        "components.waybar.opacity": 0.72,
    },
    "glaze": {
        "components.windows.blur.enabled": True,
        "components.windows.blur.size": 6,
        "components.windows.blur.passes": 2,
        "components.windows.blur.brightness": 1.05,
        "components.windows.active_opacity": 0.97,
        "components.waybar.opacity": 0.88,
    },
    "bloom": {
        "components.windows.blur.enabled": True,
        "components.windows.blur.size": 14,
        "components.windows.blur.passes": 5,
        "components.windows.blur.vibrancy": 0.35,
        "components.windows.active_opacity": 0.88,
        "components.waybar.opacity": 0.68,
    },
}

BORDER_PRESETS = {
    "minimal": {
        "components.windows.border_width": 1,
        "components.windows.active_border.style": "solid",
        "components.windows.inactive_border.opacity": 0.35,
        "components.windows.glow": 0,
    },
    "defined": {
        "components.windows.border_width": 2,
        "components.windows.active_border.style": "gradient",
        "components.windows.inactive_border.opacity": 0.66,
        "components.windows.glow": 0,
    },
    "gradient": {
        "components.windows.border_width": 2,
        "components.windows.active_border.style": "gradient",
        "components.windows.active_border.angle": 45,
        "components.windows.inactive_border.opacity": 0.55,
        "components.windows.glow": 0,
    },
    "glow": {
        "components.windows.border_width": 3,
        "components.windows.active_border.style": "gradient",
        "components.windows.active_border.angle": 45,
        "components.windows.inactive_border.opacity": 0.45,
        "components.windows.glow": 18,
        "components.windows.shadow.enabled": True,
        "components.windows.shadow.opacity": 0.55,
    },
}

WAYBAR_LAYOUT_PRESETS = {
    "full": {
        "layout": "full",
        "margin": 0,
        "radius": 0,
        "module_gap": 0,
        "module_surface": "single",
        "opacity": 0.94,
    },
    "floating": {
        "layout": "floating",
        "margin": 10,
        "radius": 12,
        "module_gap": 5,
        "module_surface": "single",
        "opacity": 0.88,
    },
    "islands": {
        "layout": "islands",
        "margin": 10,
        "radius": 14,
        "module_gap": 7,
        "module_surface": "islands",
        "opacity": 0.82,
    },
    "minimal": {
        "layout": "minimal",
        "margin": 5,
        "radius": 6,
        "module_gap": 2,
        "module_surface": "transparent",
        "opacity": 0.55,
    },
}

WINDOW_PRESETS = {
    "clean_flat": {
        "shape": "sharp",
        "texture": "clear",
        "border": "minimal",
        "shadow": "off",
    },
    "soft_glass": {
        "shape": "soft",
        "texture": "frosted",
        "border": "defined",
        "shadow": "soft",
    },
    "frosted": {
        "shape": "rounded",
        "texture": "haze",
        "border": "minimal",
        "shadow": "soft",
    },
    "sharp_technical": {
        "shape": "sharp",
        "texture": "clear",
        "border": "gradient",
        "shadow": "defined",
    },
    "retro_box": {
        "shape": "retro_box",
        "texture": "clear",
        "border": "defined",
        "shadow": "defined",
    },
    "neon_edge": {
        "shape": "soft",
        "texture": "glaze",
        "border": "glow",
        "shadow": "glow",
    },
    "borderless": {
        "shape": "soft",
        "texture": "clear",
        "border": "minimal",
        "shadow": "off",
        "border_width": 0,
    },
    "minimal_dark": {
        "shape": "sharp",
        "texture": "clear",
        "border": "minimal",
        "shadow": "soft",
    },
}

ANIMATION_PRESETS = (
    "none",
    "subtle",
    "smooth",
    "snappy",
    "bouncy",
    "dramatic",
    "glitch",
    "custom",
    "spring",
)

BASE_COMPONENTS: dict[str, Any] = {
    "windows": {
        "gaps_in": 5,
        "gaps_out": 10,
        "border_width": 2,
        "corner_radius": 10,
        "rounding_power": 2.0,
        "active_opacity": 1.0,
        "inactive_opacity": 0.92,
        "inactive_dim": 0.08,
        "blur": {
            "enabled": True,
            "size": 8,
            "passes": 3,
            "noise": 0.0117,
            "contrast": 0.8916,
            "brightness": 0.8172,
            "vibrancy": 0.1696,
        },
        "shadow": {
            "enabled": True,
            "radius": 20,
            "render_power": 3,
            "offset": "0 0",
            "color": "shadow",
            "opacity": 0.40,
        },
        "active_border": {
            "style": "gradient",
            "color": "focus",
            "color_2": "accent2",
            "angle": 45,
            "opacity": 1.0,
        },
        "inactive_border": {"color": "border_normal", "opacity": 0.66},
        "group_border": {
            "active": "accent",
            "inactive": "surface_1",
            "locked": "warning",
            "text": "on_accent",
        },
        "glow": 0,
    },
    "waybar": {
        "layout": "islands",
        "position": "top",
        "height": 34,
        "margin": 10,
        "module_gap": 6,
        "module_padding": 10,
        "font_size": 13,
        "icon_size": 18,
        "radius": 14,
        "border_width": 1,
        "border_role": "border_subtle",
        "background_role": "surface_0",
        "text_role": "text",
        "opacity": 0.82,
        "blur": True,
        "shadow": False,
        "module_surface": "islands",
        "modules": deepcopy(DEFAULT_WAYBAR_MODULES),
        "module_overrides": {},
        "workspace": {
            "inactive_role": "text_dim",
            "active_role": "accent",
            "empty_role": "disabled",
            "urgent_role": "urgent",
            "active_border_role": "accent",
            "active_background_role": "selected",
            "presentation": "numbers",
            "active_scale": 1.20,
        },
        "clock_format": "  {:%a %d %b   %H:%M}",
        "battery_warning": 25,
        "battery_critical": 10,
    },
    "launcher": {
        "provider": "wofi",
        "width": 640,
        "rows": 8,
        "padding": 10,
        "radius": 10,
        "border_width": 2,
        "background_role": "bg",
        "input_role": "bg_alt",
        "selected_role": "selected",
        "text_role": "text",
    },
    "notifications": {
        "width": 340,
        "origin": "top-right",
        "offset": "12x12",
        "padding": 12,
        "radius": 10,
        "border_width": 2,
        "timeout": 10,
        "low_role": "info",
        "normal_role": "accent",
        "critical_role": "urgent",
    },
    "terminal": {
        "opacity": 1.0,
        "padding": 0,
        "tab_bar": "fade",
        "active_tab_role": "accent",
        "inactive_tab_role": "bg_alt",
        "cursor_role": "accent",
        "selection_role": "selected",
    },
    "prompt": {
        "layout": "two_line",
        "separator": "powerline",
        "directory_role": "accent",
        "git_role": "accent2",
        "status_role": "urgent",
        "show_duration": True,
        "show_jobs": True,
        "show_battery": False,
        "show_memory": False,
        "show_time": False,
    },
    "lock_screen": {
        "clock_size": 64,
        "clock_role": "accent",
        "field_width": 280,
        "field_height": 50,
        "field_radius": 10,
        "field_role": "bg_alt",
        "outline_role": "accent",
        "text_role": "text",
        "show_avatar": False,
    },
    "homepage": {
        "enabled": False,
        "alignment": "left",
        "card_radius": 16,
        "card_opacity": 0.82,
        "show_weather": True,
        "show_system": True,
        "show_shortcuts": True,
        "density": "comfortable",
    },
    "apps": {
        "gtk_radius": 10,
        "button_role": "bg_alt",
        "button_hover_role": "hover",
        "selection_role": "selected",
        "link_role": "accent2",
        "scrollbar_role": "border_strong",
        "qt_match_gtk": True,
        "vscode_match_theme": True,
        "firefox_match_theme": True,
    },
}

STYLE_DEFAULTS = {
    "spacing_preset": "cozy",
    "shape_preset": "soft",
    "texture_preset": "frosted",
    "border_preset": "defined",
    "waybar_preset": "islands",
    "density_preset": "comfortable",
    "animation_preset": "smooth",
    "animation_speed_multiplier": 1.0,
    "workspace_style": "preset",
    "layer_animation_enabled": True,
    "layer_style": "fade",
    "custom_bezier_x1": 0.16,
    "custom_bezier_y1": 1.0,
    "custom_bezier_x2": 0.3,
    "custom_bezier_y2": 1.0,
    "spring_stiffness": 245.0,
    "spring_dampening": 22.0,
    "spring_mass": 1.0,
    "motion_blur_mode": "inherit",
    "motion_blur_samples": 4,
    "wobble_mode": "inherit",
    "wobble_intensity": 0.035,
    "wobble_stiffness": 430,
    "wobble_damping": 35,
    "wobble_mass": 1.0,
    "gaps": 10,
    "border_width": 2,
    "corner_radius": 10,
    "rounding_power": 2.0,
    "opacity": 1.0,
    "opacity_inactive": 0.92,
    "inactive_dim": 0.08,
    "blur_on": True,
    "blur_strength": 8,
    "blur_passes": 3,
    "blur_noise": 0.0117,
    "blur_contrast": 0.8916,
    "blur_brightness": 0.8172,
    "blur_vibrancy": 0.1696,
    "shadow_on": True,
    "shadow_radius": 20,
    "shadow_render_power": 3,
    "shadow_offset": "0 0",
    "shadow_color": "#000000",
    "shadow_opacity": 0.4,
    "bar_blur": True,
}


@dataclass(frozen=True)
class FieldSpec:
    path: str
    label: str
    kind: str = "number"
    minimum: float | None = None
    maximum: float | None = None
    step: float = 1.0
    choices: tuple[str, ...] = ()
    help: str = ""
    advanced: bool = False


COMPONENT_FIELDS: dict[str, tuple[FieldSpec, ...]] = {
    "windows": (
        FieldSpec("components.windows.gaps_out", "Outer gaps", "int", 0, 60, 1),
        FieldSpec("components.windows.gaps_in", "Inner gaps", "int", 0, 40, 1),
        FieldSpec("components.windows.border_width", "Border width", "int", 0, 10, 1),
        FieldSpec("components.windows.corner_radius", "Corner radius", "int", 0, 40, 1),
        FieldSpec(
            "components.windows.rounding_power",
            "Corner curvature",
            "float",
            1.0,
            8.0,
            0.1,
            advanced=True,
        ),
        FieldSpec(
            "components.windows.active_opacity",
            "Active opacity",
            "float",
            0.2,
            1.0,
            0.01,
        ),
        FieldSpec(
            "components.windows.inactive_opacity",
            "Inactive opacity",
            "float",
            0.2,
            1.0,
            0.01,
        ),
        FieldSpec(
            "components.windows.inactive_dim", "Inactive dim", "float", 0.0, 1.0, 0.01
        ),
        FieldSpec("components.windows.blur.enabled", "Blur", "bool"),
        FieldSpec("components.windows.blur.size", "Blur size", "int", 1, 30, 1),
        FieldSpec("components.windows.blur.passes", "Blur passes", "int", 1, 8, 1),
        FieldSpec(
            "components.windows.blur.noise",
            "Blur noise",
            "float",
            0.0,
            0.20,
            0.001,
            advanced=True,
        ),
        FieldSpec(
            "components.windows.blur.contrast",
            "Blur contrast",
            "float",
            0.0,
            2.0,
            0.01,
            advanced=True,
        ),
        FieldSpec(
            "components.windows.blur.brightness",
            "Blur brightness",
            "float",
            0.0,
            2.0,
            0.01,
            advanced=True,
        ),
        FieldSpec(
            "components.windows.blur.vibrancy",
            "Blur vibrancy",
            "float",
            0.0,
            1.0,
            0.01,
            advanced=True,
        ),
        FieldSpec("components.windows.shadow.enabled", "Shadow", "bool"),
        FieldSpec("components.windows.shadow.radius", "Shadow radius", "int", 0, 60, 1),
        FieldSpec(
            "components.windows.shadow.render_power",
            "Shadow sharpness",
            "int",
            1,
            4,
            1,
            advanced=True,
        ),
        FieldSpec(
            "components.windows.shadow.opacity",
            "Shadow opacity",
            "float",
            0.0,
            1.0,
            0.01,
        ),
        FieldSpec(
            "components.windows.active_border.color", "Active border role", "role"
        ),
        FieldSpec("components.windows.active_border.color_2", "Gradient role", "role"),
        FieldSpec(
            "components.windows.active_border.angle", "Gradient angle", "int", 0, 360, 5
        ),
        FieldSpec(
            "components.windows.inactive_border.color", "Inactive border role", "role"
        ),
        FieldSpec(
            "components.windows.inactive_border.opacity",
            "Inactive border opacity",
            "float",
            0.0,
            1.0,
            0.01,
        ),
        FieldSpec("components.windows.glow", "Border glow", "int", 0, 40, 1),
        FieldSpec(
            "style.animation_preset", "Animation", "choice", choices=ANIMATION_PRESETS
        ),
        FieldSpec(
            "style.animation_speed_multiplier",
            "Animation duration",
            "float",
            0.25,
            3.0,
            0.05,
            help="Lower is faster; higher is slower.",
        ),
        FieldSpec(
            "style.workspace_style",
            "Workspace transition",
            "choice",
            choices=(
                "preset",
                "slide",
                "slidevert",
                "fade",
                "slidefade",
                "slidefadevert",
            ),
        ),
        FieldSpec(
            "style.layer_animation_enabled", "Animate popups and launchers", "bool"
        ),
        FieldSpec(
            "style.layer_style",
            "Popup and launcher style",
            "choice",
            choices=("fade", "slide"),
        ),
        FieldSpec(
            "style.custom_bezier_x1",
            "Custom curve start timing",
            "float",
            0.0,
            1.0,
            0.01,
            advanced=True,
        ),
        FieldSpec(
            "style.custom_bezier_y1",
            "Custom curve bounce",
            "float",
            -1.0,
            2.0,
            0.01,
            advanced=True,
        ),
        FieldSpec(
            "style.custom_bezier_x2",
            "Custom curve end timing",
            "float",
            0.0,
            1.0,
            0.01,
            advanced=True,
        ),
        FieldSpec(
            "style.custom_bezier_y2",
            "Custom curve settle",
            "float",
            -1.0,
            2.0,
            0.01,
            advanced=True,
        ),
        FieldSpec(
            "style.spring_stiffness", "Spring responsiveness", "float", 50.0, 600.0, 5.0
        ),
        FieldSpec(
            "style.spring_dampening",
            "Spring damping",
            "float",
            5.0,
            60.0,
            1.0,
            help="Lower values bounce more.",
        ),
        FieldSpec(
            "style.spring_mass", "Spring weight", "float", 0.2, 3.0, 0.1, advanced=True
        ),
        FieldSpec(
            "style.motion_blur_mode",
            "Motion blur",
            "choice",
            choices=("inherit", "enabled", "disabled"),
        ),
        FieldSpec(
            "style.motion_blur_samples",
            "Motion blur quality",
            "int",
            1,
            10,
            1,
            advanced=True,
        ),
        FieldSpec(
            "style.wobble_mode",
            "Window wobble",
            "choice",
            choices=("inherit", "enabled", "disabled"),
        ),
        FieldSpec("style.wobble_intensity", "Wobble amount", "float", 0.0, 0.2, 0.005),
        FieldSpec(
            "style.wobble_stiffness",
            "Wobble responsiveness",
            "int",
            50,
            800,
            10,
            advanced=True,
        ),
        FieldSpec(
            "style.wobble_damping", "Wobble damping", "int", 1, 100, 1, advanced=True
        ),
        FieldSpec(
            "style.wobble_mass", "Wobble weight", "float", 0.1, 4.0, 0.1, advanced=True
        ),
    ),
    "waybar": (
        FieldSpec(
            "components.waybar.layout",
            "Layout",
            "choice",
            choices=tuple(WAYBAR_LAYOUT_PRESETS),
        ),
        FieldSpec(
            "components.waybar.position",
            "Position",
            "choice",
            choices=("top", "bottom"),
        ),
        FieldSpec("components.waybar.height", "Height", "int", 20, 80, 1),
        FieldSpec("components.waybar.margin", "Outer margin", "int", 0, 40, 1),
        FieldSpec("components.waybar.module_gap", "Module gap", "int", 0, 30, 1),
        FieldSpec(
            "components.waybar.module_padding", "Module padding", "int", 0, 30, 1
        ),
        FieldSpec("components.waybar.font_size", "Font size", "int", 8, 32, 1),
        FieldSpec("components.waybar.icon_size", "Icon size", "int", 8, 40, 1),
        FieldSpec("components.waybar.radius", "Corner radius", "int", 0, 40, 1),
        FieldSpec("components.waybar.border_width", "Border width", "int", 0, 6, 1),
        FieldSpec("components.waybar.border_role", "Border role", "role"),
        FieldSpec("components.waybar.background_role", "Background role", "role"),
        FieldSpec("components.waybar.text_role", "Text role", "role"),
        FieldSpec("components.waybar.opacity", "Opacity", "float", 0.0, 1.0, 0.01),
        FieldSpec("components.waybar.blur", "Blur", "bool"),
        FieldSpec("components.waybar.shadow", "Shadow", "bool"),
        FieldSpec(
            "components.waybar.workspace.inactive_role", "Inactive workspace", "role"
        ),
        FieldSpec(
            "components.waybar.workspace.active_role", "Active workspace", "role"
        ),
        FieldSpec("components.waybar.workspace.empty_role", "Empty workspace", "role"),
        FieldSpec(
            "components.waybar.workspace.urgent_role", "Urgent workspace", "role"
        ),
        FieldSpec("components.waybar.clock_format", "Clock format", "text"),
        FieldSpec(
            "components.waybar.battery_warning", "Battery warning", "int", 1, 100, 1
        ),
        FieldSpec(
            "components.waybar.battery_critical", "Battery critical", "int", 1, 100, 1
        ),
    ),
    "launcher": (
        FieldSpec(
            "components.launcher.provider",
            "Launcher",
            "choice",
            choices=("wofi", "rofi"),
        ),
        FieldSpec("components.launcher.width", "Width", "int", 280, 1600, 10),
        FieldSpec("components.launcher.rows", "Rows", "int", 3, 30, 1),
        FieldSpec("components.launcher.padding", "Padding", "int", 0, 40, 1),
        FieldSpec("components.launcher.radius", "Corner radius", "int", 0, 40, 1),
        FieldSpec("components.launcher.border_width", "Border width", "int", 0, 8, 1),
        FieldSpec("components.launcher.background_role", "Background role", "role"),
        FieldSpec("components.launcher.input_role", "Input role", "role"),
        FieldSpec("components.launcher.selected_role", "Selection role", "role"),
        FieldSpec("components.launcher.text_role", "Text role", "role"),
    ),
    "notifications": (
        FieldSpec("components.notifications.width", "Width", "int", 220, 900, 10),
        FieldSpec(
            "components.notifications.origin",
            "Position",
            "choice",
            choices=(
                "top-left",
                "top-center",
                "top-right",
                "bottom-left",
                "bottom-center",
                "bottom-right",
            ),
        ),
        FieldSpec("components.notifications.padding", "Padding", "int", 0, 40, 1),
        FieldSpec("components.notifications.radius", "Corner radius", "int", 0, 40, 1),
        FieldSpec(
            "components.notifications.border_width", "Border width", "int", 0, 8, 1
        ),
        FieldSpec("components.notifications.timeout", "Timeout", "int", 0, 60, 1),
        FieldSpec("components.notifications.low_role", "Low urgency role", "role"),
        FieldSpec(
            "components.notifications.normal_role", "Normal urgency role", "role"
        ),
        FieldSpec(
            "components.notifications.critical_role", "Critical urgency role", "role"
        ),
    ),
    "terminal": (
        FieldSpec(
            "components.terminal.opacity", "Background opacity", "float", 0.1, 1.0, 0.01
        ),
        FieldSpec("components.terminal.padding", "Window padding", "int", 0, 40, 1),
        FieldSpec(
            "components.terminal.tab_bar",
            "Tab bar style",
            "choice",
            choices=("hidden", "fade", "powerline", "slant", "separator"),
        ),
        FieldSpec("components.terminal.active_tab_role", "Active tab role", "role"),
        FieldSpec("components.terminal.inactive_tab_role", "Inactive tab role", "role"),
        FieldSpec("components.terminal.cursor_role", "Cursor role", "role"),
        FieldSpec("components.terminal.selection_role", "Selection role", "role"),
    ),
    "prompt": (
        FieldSpec(
            "components.prompt.layout",
            "Prompt layout",
            "choice",
            choices=("one_line", "two_line"),
        ),
        FieldSpec(
            "components.prompt.separator",
            "Separator",
            "choice",
            choices=("powerline", "rounded", "block", "minimal"),
        ),
        FieldSpec("components.prompt.directory_role", "Directory role", "role"),
        FieldSpec("components.prompt.git_role", "Git role", "role"),
        FieldSpec("components.prompt.status_role", "Status role", "role"),
        FieldSpec("components.prompt.show_duration", "Show duration", "bool"),
        FieldSpec("components.prompt.show_jobs", "Show jobs", "bool"),
        FieldSpec("components.prompt.show_battery", "Show battery", "bool"),
        FieldSpec("components.prompt.show_memory", "Show memory", "bool"),
        FieldSpec("components.prompt.show_time", "Show time", "bool"),
    ),
    "lock_screen": (
        FieldSpec("components.lock_screen.clock_size", "Clock size", "int", 16, 160, 1),
        FieldSpec("components.lock_screen.clock_role", "Clock role", "role"),
        FieldSpec(
            "components.lock_screen.field_width", "Field width", "int", 160, 800, 10
        ),
        FieldSpec(
            "components.lock_screen.field_height", "Field height", "int", 30, 160, 5
        ),
        FieldSpec(
            "components.lock_screen.field_radius", "Field radius", "int", 0, 50, 1
        ),
        FieldSpec("components.lock_screen.field_role", "Field role", "role"),
        FieldSpec("components.lock_screen.outline_role", "Outline role", "role"),
        FieldSpec("components.lock_screen.text_role", "Text role", "role"),
        FieldSpec("components.lock_screen.show_avatar", "Show avatar", "bool"),
    ),
    "homepage": (
        FieldSpec("components.homepage.enabled", "Enabled", "bool"),
        FieldSpec(
            "components.homepage.alignment",
            "Alignment",
            "choice",
            choices=("left", "right"),
        ),
        FieldSpec("components.homepage.card_radius", "Card radius", "int", 0, 50, 1),
        FieldSpec(
            "components.homepage.card_opacity", "Card opacity", "float", 0.0, 1.0, 0.01
        ),
        FieldSpec("components.homepage.show_weather", "Weather card", "bool"),
        FieldSpec("components.homepage.show_system", "System card", "bool"),
        FieldSpec("components.homepage.show_shortcuts", "Shortcut card", "bool"),
        FieldSpec(
            "components.homepage.density",
            "Density",
            "choice",
            choices=("compact", "comfortable", "spacious"),
        ),
    ),
    "apps": (
        FieldSpec("components.apps.gtk_radius", "GTK corner radius", "int", 0, 40, 1),
        FieldSpec("components.apps.button_role", "Button role", "role"),
        FieldSpec("components.apps.button_hover_role", "Button hover role", "role"),
        FieldSpec("components.apps.selection_role", "Selection role", "role"),
        FieldSpec("components.apps.link_role", "Link role", "role"),
        FieldSpec("components.apps.scrollbar_role", "Scrollbar role", "role"),
        FieldSpec("components.apps.qt_match_gtk", "Match Qt to GTK", "bool"),
        FieldSpec("components.apps.vscode_match_theme", "Theme VS Code", "bool"),
        FieldSpec("components.apps.firefox_match_theme", "Theme Firefox", "bool"),
    ),
}

COMPONENT_LABELS = {
    "windows": "Windows",
    "waybar": "Waybar",
    "launcher": "Launcher",
    "notifications": "Notifications",
    "terminal": "Terminal",
    "prompt": "Prompt",
    "lock_screen": "Lock Screen",
    "homepage": "Homepage",
    "apps": "Apps",
}


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"invalid color: {hex_color}")
    return int(value[:2], 16), int(value[2:4], 16), int(value[4:], 16)


def _hex(rgb: Iterable[float]) -> str:
    vals = [max(0, min(255, round(v))) for v in rgb]
    return "#" + "".join(f"{v:02x}" for v in vals)


def blend(c1: str, c2: str, ratio: float) -> str:
    a, b = _rgb(c1), _rgb(c2)
    t = max(0.0, min(1.0, float(ratio)))
    return _hex(x + (y - x) * t for x, y in zip(a, b))


def relative_luminance(color: str) -> float:
    def channel(v: int) -> float:
        c = v / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = _rgb(color)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(c1: str, c2: str) -> float:
    l1, l2 = relative_luminance(c1), relative_luminance(c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def best_contrast(bg: str, candidates: Iterable[str]) -> str:
    return max(candidates, key=lambda c: contrast_ratio(bg, c))


def resolve_roles(roles: dict[str, str]) -> dict[str, str]:
    r = dict(roles)
    bg = r.get("bg", "#111111")
    bg_alt = r.get("bg_alt", blend(bg, "#ffffff", 0.08))
    text = r.get("text", "#eeeeee")
    text_dim = r.get("text_dim", blend(text, bg, 0.35))
    accent = r.get("accent", "#7aa2f7")
    accent2 = r.get("accent2", accent)
    urgent = r.get("urgent", "#f7768e")
    focus = r.get("focus", accent)
    border_normal = r.get("border_normal", bg_alt)
    defaults = {
        "surface_0": bg,
        "surface_1": bg_alt,
        "surface_2": blend(bg_alt, text, 0.08),
        "overlay": bg,
        "hover": blend(bg_alt, accent, 0.15),
        "selected": accent,
        "border_subtle": border_normal,
        "border_strong": focus,
        "success": r.get("ansi_green", accent2),
        "warning": r.get("ansi_yellow", accent2),
        "info": r.get("ansi_blue", accent2),
        "disabled": text_dim,
        "shadow": "#000000",
        "on_accent": best_contrast(accent, [bg, text, "#000000", "#ffffff"]),
        "on_urgent": best_contrast(urgent, [bg, text, "#000000", "#ffffff"]),
    }
    for key, value in defaults.items():
        r.setdefault(key, value)
    return r


def deep_get(data: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def deep_set(data: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cur: dict[str, Any] = data
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def ensure_theme_schema(theme: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(theme)
    out.setdefault("version", 3)
    out.setdefault("dark", True)
    out["style"] = deep_merge(STYLE_DEFAULTS, out.get("style", {}))
    out["components"] = deep_merge(BASE_COMPONENTS, out.get("components", {}))
    out["roles"] = resolve_roles(out.get("roles", {}))
    out.setdefault("studio", {})
    out["studio"].setdefault("locks", [])
    out["studio"].setdefault("notes", "")
    synchronize_style(out)
    return out


def synchronize_style(theme: dict[str, Any]) -> None:
    """Keep legacy style keys in sync with the richer component schema."""
    style = theme.setdefault("style", {})
    windows = theme.setdefault("components", {}).setdefault("windows", {})
    style["gaps"] = int(windows.get("gaps_out", style.get("gaps", 10)))
    style["border_width"] = int(
        windows.get("border_width", style.get("border_width", 2))
    )
    style["corner_radius"] = int(
        windows.get("corner_radius", style.get("corner_radius", 10))
    )
    style["rounding_power"] = float(
        windows.get("rounding_power", style.get("rounding_power", 2.0))
    )
    style["opacity"] = float(windows.get("active_opacity", style.get("opacity", 1.0)))
    style["opacity_inactive"] = float(
        windows.get("inactive_opacity", style.get("opacity_inactive", 0.92))
    )
    style["inactive_dim"] = float(
        windows.get("inactive_dim", style.get("inactive_dim", 0.08))
    )
    blur = windows.get("blur", {})
    style["blur_on"] = bool(blur.get("enabled", style.get("blur_on", True)))
    style["blur_strength"] = int(blur.get("size", style.get("blur_strength", 8)))
    style["blur_passes"] = int(blur.get("passes", style.get("blur_passes", 3)))
    style["blur_noise"] = float(blur.get("noise", style.get("blur_noise", 0.0117)))
    style["blur_contrast"] = float(
        blur.get("contrast", style.get("blur_contrast", 0.8916))
    )
    style["blur_brightness"] = float(
        blur.get("brightness", style.get("blur_brightness", 0.8172))
    )
    style["blur_vibrancy"] = float(
        blur.get("vibrancy", style.get("blur_vibrancy", 0.1696))
    )
    shadow = windows.get("shadow", {})
    style["shadow_on"] = bool(shadow.get("enabled", style.get("shadow_on", True)))
    style["shadow_radius"] = int(shadow.get("radius", style.get("shadow_radius", 20)))
    style["shadow_render_power"] = int(
        shadow.get("render_power", style.get("shadow_render_power", 3))
    )
    style["shadow_offset"] = str(
        shadow.get("offset", style.get("shadow_offset", "0 0"))
    )
    style["shadow_opacity"] = float(
        shadow.get("opacity", style.get("shadow_opacity", 0.4))
    )
    shadow_role = shadow.get("color", "shadow")
    style["shadow_color"] = resolve_roles(theme.get("roles", {})).get(
        shadow_role, shadow_role if is_hex(shadow_role) else "#000000"
    )
    waybar = theme.get("components", {}).get("waybar", {})
    style["bar_blur"] = bool(waybar.get("blur", style.get("bar_blur", False)))


def apply_mapping(theme: dict[str, Any], mapping: dict[str, Any]) -> None:
    for path, value in mapping.items():
        deep_set(theme, path, deepcopy(value))
    synchronize_style(theme)


def apply_axis(theme: dict[str, Any], axis: str, name: str) -> None:
    mapping_table = {
        "spacing": SPACING_PRESETS,
        "density": DENSITY_PRESETS,
        "shape": SHAPE_PRESETS,
        "texture": TEXTURE_PRESETS,
        "border": BORDER_PRESETS,
    }
    if axis == "waybar":
        if name not in WAYBAR_LAYOUT_PRESETS:
            raise KeyError(name)
        deep_set(theme, "style.waybar_preset", name)
        for key, value in WAYBAR_LAYOUT_PRESETS[name].items():
            deep_set(theme, f"components.waybar.{key}", deepcopy(value))
        synchronize_style(theme)
        return
    if axis == "animation":
        if name not in ANIMATION_PRESETS:
            raise KeyError(name)
        deep_set(theme, "style.animation_preset", name)
        return
    table = mapping_table[axis]
    if name not in table:
        raise KeyError(name)
    deep_set(theme, f"style.{axis}_preset", name)
    apply_mapping(theme, table[name])


def apply_window_preset(theme: dict[str, Any], name: str) -> None:
    preset = WINDOW_PRESETS[name]
    apply_axis(theme, "shape", str(preset["shape"]))
    apply_axis(theme, "texture", str(preset["texture"]))
    apply_axis(theme, "border", str(preset["border"]))
    if preset.get("shadow") == "off":
        deep_set(theme, "components.windows.shadow.enabled", False)
    elif preset.get("shadow") == "glow":
        deep_set(theme, "components.windows.shadow.enabled", True)
        deep_set(theme, "components.windows.shadow.radius", 32)
        deep_set(theme, "components.windows.shadow.opacity", 0.55)
    elif preset.get("shadow") == "defined":
        deep_set(theme, "components.windows.shadow.enabled", True)
        deep_set(theme, "components.windows.shadow.radius", 14)
        deep_set(theme, "components.windows.shadow.opacity", 0.45)
    else:
        deep_set(theme, "components.windows.shadow.enabled", True)
        deep_set(theme, "components.windows.shadow.radius", 20)
        deep_set(theme, "components.windows.shadow.opacity", 0.32)
    if "border_width" in preset:
        deep_set(theme, "components.windows.border_width", preset["border_width"])
    synchronize_style(theme)


def is_hex(value: Any) -> bool:
    return isinstance(value, str) and bool(HEX_RE.fullmatch(value))


def role_color(theme: dict[str, Any], value: str, fallback: str = "#ffffff") -> str:
    if is_hex(value):
        return value
    return resolve_roles(theme.get("roles", {})).get(value, fallback)


def color_variants(color: str) -> dict[str, str]:
    r, g, b = (v / 255.0 for v in _rgb(color))
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    def mk(dl: float, ds: float = 0.0) -> str:
        rr, gg, bb = colorsys.hls_to_rgb(
            h, max(0.0, min(1.0, l + dl)), max(0.0, min(1.0, s + ds))
        )
        return _hex((rr * 255, gg * 255, bb * 255))

    return {
        "darker": mk(-0.18),
        "dark": mk(-0.10),
        "base": color.lower(),
        "light": mk(0.10),
        "lighter": mk(0.18),
        "muted": mk(0.0, -0.25),
        "vivid": mk(0.0, 0.18),
    }


def generate_palette_from_seed(seed: str, dark: bool = True) -> dict[str, str]:
    variants = color_variants(seed)
    if dark:
        bg = blend(variants["darker"], "#000000", 0.62)
        bg_alt = blend(bg, seed, 0.12)
        text = best_contrast(bg, ["#f8f8f2", "#ffffff", "#e8e8ec"])
        text_dim = blend(text, bg, 0.38)
    else:
        bg = blend(variants["lighter"], "#ffffff", 0.76)
        bg_alt = blend(bg, seed, 0.08)
        text = best_contrast(bg, ["#101014", "#202028", "#000000"])
        text_dim = blend(text, bg, 0.42)
    accent2 = color_variants(seed)["light" if dark else "dark"]
    urgent = "#ff5f78" if dark else "#c62848"
    roles = {
        "bg": bg,
        "bg_alt": bg_alt,
        "text": text,
        "text_dim": text_dim,
        "accent": seed.lower(),
        "accent2": accent2,
        "urgent": urgent,
        "focus": seed.lower(),
        "border_normal": blend(bg_alt, text, 0.16),
    }
    return resolve_roles(roles)


def extract_wallpaper_palette(
    path: str | os.PathLike[str], count: int = 8
) -> list[str]:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Wallpaper palette extraction needs Pillow (python-pillow)."
        ) from exc
    image = Image.open(path).convert("RGB")
    image.thumbnail((240, 240))
    quantized = image.quantize(
        colors=max(3, min(16, count)), method=Image.Quantize.MEDIANCUT
    )
    palette = quantized.getpalette() or []
    counts = sorted(quantized.getcolors() or [], reverse=True)
    result: list[str] = []
    for _, index in counts:
        if not isinstance(index, int):
            continue
        start = index * 3
        if start + 2 >= len(palette):
            continue
        color = _hex(palette[start : start + 3])
        if all(math.dist(_rgb(color), _rgb(old)) > 36 for old in result):
            result.append(color)
        if len(result) >= count:
            break
    return result


def palette_from_wallpaper(
    path: str | os.PathLike[str], dark: bool = True
) -> dict[str, str]:
    colors = extract_wallpaper_palette(path, 10)
    if not colors:
        raise RuntimeError("No colors could be extracted from the wallpaper.")
    colors = sorted(colors, key=relative_luminance)
    if dark:
        bg = colors[0]
        bg_alt = colors[min(2, len(colors) - 1)]
        text = colors[-1]
        accent_candidates = colors[2:-1] or colors
    else:
        bg = colors[-1]
        bg_alt = colors[max(0, len(colors) - 3)]
        text = colors[0]
        accent_candidates = colors[1:-2] or colors
    accent = max(
        accent_candidates,
        key=lambda c: abs(relative_luminance(c) - relative_luminance(bg)),
    )
    accent2 = max(accent_candidates, key=lambda c: contrast_ratio(c, accent))
    urgent = "#ff5f78" if dark else "#c62848"
    roles = {
        "bg": bg,
        "bg_alt": bg_alt,
        "text": text,
        "text_dim": blend(text, bg, 0.38),
        "accent": accent,
        "accent2": accent2,
        "urgent": urgent,
        "focus": accent,
        "border_normal": blend(bg_alt, text, 0.16),
    }
    return resolve_roles(roles)


def _validation_item(level: str, path: str, message: str) -> dict[str, str]:
    return {"level": level, "path": path, "message": message}


def validate_theme(theme: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    roles = theme.get("roles")
    if not isinstance(roles, dict):
        return [_validation_item("error", "roles", "Theme has no role map.")]
    for role in CORE_ROLES:
        value = roles.get(role)
        if value is None:
            issues.append(
                _validation_item(
                    "error", f"roles.{role}", f"Missing required color role: {role}."
                )
            )
        elif not is_hex(value):
            issues.append(
                _validation_item(
                    "error", f"roles.{role}", f"{role} must be a six-digit hex color."
                )
            )
    for role, value in roles.items():
        if not is_hex(value):
            issues.append(
                _validation_item("error", f"roles.{role}", f"Invalid color: {value!r}.")
            )
    resolved = resolve_roles({k: v for k, v in roles.items() if is_hex(v)})
    pairs = (
        ("text", "bg", 4.5),
        ("text", "surface_0", 4.5),
        ("text_dim", "bg", 3.0),
        ("on_accent", "accent", 4.5),
        ("on_urgent", "urgent", 4.5),
    )
    for fg, bg, minimum in pairs:
        ratio = contrast_ratio(resolved[fg], resolved[bg])
        if ratio < minimum:
            issues.append(
                _validation_item(
                    "warning",
                    f"roles.{fg}",
                    f"{ROLE_LABELS.get(fg, fg)} contrast on {ROLE_LABELS.get(bg, bg)} is {ratio:.1f}:1; target {minimum:.1f}:1.",
                )
            )
    ensured = ensure_theme_schema(theme)
    for fields in COMPONENT_FIELDS.values():
        for field in fields:
            value = deep_get(ensured, field.path)
            if field.kind in ("int", "float") and isinstance(value, (int, float)):
                if field.minimum is not None and value < field.minimum:
                    issues.append(
                        _validation_item(
                            "error",
                            field.path,
                            f"{field.label} is below {field.minimum}.",
                        )
                    )
                if field.maximum is not None and value > field.maximum:
                    issues.append(
                        _validation_item(
                            "error",
                            field.path,
                            f"{field.label} is above {field.maximum}.",
                        )
                    )
            elif field.kind == "choice" and value not in field.choices:
                issues.append(
                    _validation_item(
                        "error",
                        field.path,
                        f"Unknown {field.label.lower()}: {value!r}.",
                    )
                )
            elif field.kind == "role" and not (is_hex(value) or value in resolved):
                issues.append(
                    _validation_item(
                        "error", field.path, f"Unknown palette role: {value!r}."
                    )
                )
    passes = deep_get(ensured, "components.windows.blur.passes", 3)
    if isinstance(passes, int) and passes > 5:
        issues.append(
            _validation_item(
                "warning",
                "components.windows.blur.passes",
                "More than five blur passes may reduce performance.",
            )
        )
    waybar = ensured["components"]["waybar"]
    known = set(
        DEFAULT_WAYBAR_MODULES["left"]
        + DEFAULT_WAYBAR_MODULES["center"]
        + DEFAULT_WAYBAR_MODULES["right"]
        + [
            "battery",
            "cpu",
            "memory",
            "temperature",
            "hyprland/workspaces",
            "hyprland/window",
            "custom/launcher",
        ]
    )
    seen: set[str] = set()
    for side in ("left", "center", "right"):
        modules = waybar.get("modules", {}).get(side, [])
        if not isinstance(modules, list):
            issues.append(
                _validation_item(
                    "error",
                    f"components.waybar.modules.{side}",
                    "Waybar module group must be a list.",
                )
            )
            continue
        for module in modules:
            if module in seen:
                issues.append(
                    _validation_item(
                        "warning",
                        f"components.waybar.modules.{side}",
                        f"Waybar module {module} appears more than once.",
                    )
                )
            seen.add(module)
            if module not in known and not str(module).startswith("custom/"):
                issues.append(
                    _validation_item(
                        "warning",
                        f"components.waybar.modules.{side}",
                        f"Unknown Waybar module: {module}.",
                    )
                )
    warning = int(waybar.get("battery_warning", 25))
    critical = int(waybar.get("battery_critical", 10))
    if critical >= warning:
        issues.append(
            _validation_item(
                "warning",
                "components.waybar.battery_critical",
                "Battery critical threshold should be lower than warning threshold.",
            )
        )
    return issues


def validation_summary(issues: list[dict[str, str]]) -> tuple[int, int]:
    return sum(i["level"] == "error" for i in issues), sum(
        i["level"] == "warning" for i in issues
    )


def search_index() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for component, fields in COMPONENT_FIELDS.items():
        label = COMPONENT_LABELS[component]
        for field in fields:
            items.append(
                {
                    "label": f"{label} › {field.label}",
                    "path": field.path,
                    "component": component,
                    "help": field.help,
                }
            )
    for role in ALL_ROLES:
        items.append(
            {
                "label": f"Palette › {ROLE_LABELS.get(role, role)}",
                "path": f"roles.{role}",
                "component": "palette",
                "help": role,
            }
        )
    for axis, names in (
        ("Spacing", SPACING_PRESETS),
        ("Shape", SHAPE_PRESETS),
        ("Texture", TEXTURE_PRESETS),
        ("Borders", BORDER_PRESETS),
        ("Waybar", WAYBAR_LAYOUT_PRESETS),
    ):
        for name in names:
            items.append(
                {
                    "label": f"Quick Style › {axis} › {name.replace('_', ' ').title()}",
                    "path": f"quick.{axis.lower()}.{name}",
                    "component": "quick",
                    "help": "preset",
                }
            )
    return items


def dump_json(theme: dict[str, Any]) -> str:
    return json.dumps(theme, indent=2, ensure_ascii=False) + "\n"


def safe_theme_name(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "_", name.strip()).strip("._-")
    if not value:
        raise ValueError("Theme name cannot be empty.")
    return value
