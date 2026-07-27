"""Effects-profile system for Hyprland desktop effects.

Provides named presets (minimal, calm, polished, cyber) that override
a theme's style values and generate Hyprland animation config.
"""

import json
import os
import tempfile

PROFILE_PATH = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "theme-engine", "effects.json",
)

PRESETS = {
    "minimal": {
        "blur_on": "false",
        "blur_strength": 0,
        "shadow_on": "false",
        "shadow_radius": 0,
        "shadow_opacity": 0,
        "inactive_dim": 0,
        "border_width": 1,
        "anim_enabled": False,
        "reduced_motion": True,
        "animations": [],
    },
    "calm": {
        "blur_on": "true",
        "blur_strength": 6,
        "shadow_on": "true",
        "shadow_radius": 15,
        "shadow_opacity": 0.3,
        "inactive_dim": 0.05,
        "border_width": 2,
        "anim_enabled": True,
        "reduced_motion": False,
        "animations": [
            "bezier = gentle, 0.4, 0.0, 0.2, 1.0",
            "animation = windowsIn, 1, 6, gentle, slide",
            "animation = windowsOut, 1, 4, gentle, fade",
            "animation = fade, 1, 5, gentle",
            "animation = workspaces, 1, 5, gentle, slide",
        ],
    },
    "polished": {
        "blur_on": "true",
        "blur_strength": 10,
        "shadow_on": "true",
        "shadow_radius": 22,
        "shadow_opacity": 0.45,
        "inactive_dim": 0.12,
        "border_width": 2,
        "anim_enabled": True,
        "reduced_motion": False,
        "animations": [
            "bezier = smooth, 0.25, 0.1, 0.25, 1.0",
            "animation = windowsIn, 1, 5, smooth, slide",
            "animation = windowsOut, 1, 5, smooth, slide",
            "animation = fade, 1, 4, smooth",
            "animation = workspaces, 1, 4, smooth, slide",
        ],
    },
    "cyber": {
        "blur_on": "true",
        "blur_strength": 14,
        "shadow_on": "true",
        "shadow_radius": 30,
        "shadow_opacity": 0.6,
        "inactive_dim": 0.2,
        "border_width": 3,
        "anim_enabled": True,
        "reduced_motion": False,
        "animations": [
            "bezier = flash, 0.1, 0.9, 0.2, 1.0",
            "animation = windowsIn, 1, 4, flash, popin 80%",
            "animation = windowsOut, 1, 3, flash, popin 80%",
            "animation = fade, 1, 3, flash",
            "animation = workspaces, 1, 3, flash, slidefade 40%",
        ],
    },
}

PRESET_NAMES = list(PRESETS.keys())

STYLE_KEYS = [
    "blur_on", "blur_strength", "shadow_on", "shadow_radius",
    "shadow_opacity", "inactive_dim", "border_width",
]


def validate_preset(name):
    return name in PRESETS


def list_presets():
    return list(PRESET_NAMES)


def profile():
    try:
        with open(PROFILE_PATH) as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    preset = raw.get("preset")
    if preset and validate_preset(preset):
        return preset
    return None


def save(preset_name):
    if preset_name is not None and not validate_preset(preset_name):
        raise ValueError(f"unknown effects preset: {preset_name}")
    directory = os.path.dirname(PROFILE_PATH)
    os.makedirs(directory, exist_ok=True)
    data = {"version": 1, "preset": preset_name}
    fd, tmp = tempfile.mkstemp(prefix="effects.", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, PROFILE_PATH)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def resolve(style, preset_name):
    if preset_name is None:
        return dict(style)
    if not validate_preset(preset_name):
        raise ValueError(f"unknown effects preset: {preset_name}")
    merged = dict(style)
    preset = PRESETS[preset_name]
    for key in STYLE_KEYS:
        if key in preset:
            merged[key] = preset[key]
    return merged


def render_animations(preset_name):
    if preset_name is None:
        return []
    if not validate_preset(preset_name):
        raise ValueError(f"unknown effects preset: {preset_name}")
    preset = PRESETS[preset_name]
    if not preset["anim_enabled"]:
        return [
            "",
            "animations {",
            "    enabled = false",
            "}",
        ]
    lines = [
        "",
        "animations {",
        "    enabled = true",
    ]
    for anim_line in preset["animations"]:
        lines.append(f"    {anim_line}")
    lines.append("}")
    return lines
