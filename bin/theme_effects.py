"""Effects-profile system for Hyprland desktop effects.

Three independent axes:
  - shape:   geometry (gaps, corner radius, rounding curve, border width)
  - texture: surface treatment (blur, opacity, shadows, dim)
  - anim:    motion style (animation curves, speeds, entrance/exit types)

All are optional and stored independently in effects.json.
"""

import json
import os
import tempfile

PROFILE_PATH = os.path.join(
    os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
    "theme-engine", "effects.json",
)

# ── Shapes: geometry overrides ─────────────────────────────────────────

SHAPES = {
    "sharp": {
        "corner_radius_offset": -12,
        "rounding_power": 5.0,
        "border_width": 1,
        "gaps_offset": -6,
    },
    "rounded": {
        "corner_radius_offset": 0,
        "rounding_power": 2.0,
        "border_width": 2,
        "gaps_offset": 0,
    },
    "pillowy": {
        "corner_radius_offset": 8,
        "rounding_power": 1.5,
        "border_width": 1,
        "gaps_offset": 8,
    },
    "boxy": {
        "corner_radius_offset": -4,
        "rounding_power": 4.0,
        "border_width": 3,
        "gaps_offset": -6,
    },
}

# ── Textures: surface treatment overrides ──────────────────────────────

TEXTURES = {
    "clear": {
        "blur_on": "false",
        "blur_strength": 0,
        "blur_passes": 1,
        "blur_noise": 0.0,
        "blur_contrast": 1.0,
        "blur_brightness": 1.0,
        "blur_vibrancy": 0.0,
        "shadow_on": "false",
        "shadow_radius": 0,
        "shadow_opacity": 0,
        "shadow_render_power": 3,
        "shadow_offset": "0 0",
        "inactive_dim": 0,
        "opacity_offset": 0.08,
        "opacity_inactive_offset": 0.1,
        "bar_blur": False,
    },
    "frosted": {
        "blur_on": "true",
        "blur_strength": 16,
        "blur_passes": 4,
        "blur_noise": 0.02,
        "blur_contrast": 0.75,
        "blur_brightness": 0.72,
        "blur_vibrancy": 0.1,
        "shadow_on": "true",
        "shadow_radius": 18,
        "shadow_opacity": 0.3,
        "shadow_render_power": 2,
        "shadow_offset": "0 4",
        "inactive_dim": 0.06,
        "opacity_offset": -0.12,
        "opacity_inactive_offset": -0.16,
        "bar_blur": True,
    },
    "glaze": {
        "blur_on": "true",
        "blur_strength": 18,
        "blur_passes": 4,
        "blur_noise": 0.0,
        "blur_contrast": 0.9,
        "blur_brightness": 0.95,
        "blur_vibrancy": 0.5,
        "shadow_on": "true",
        "shadow_radius": 10,
        "shadow_opacity": 0.15,
        "shadow_render_power": 3,
        "shadow_offset": "0 2",
        "inactive_dim": 0.02,
        "opacity_offset": -0.18,
        "opacity_inactive_offset": -0.22,
        "bar_blur": True,
    },
    "haze": {
        "blur_on": "true",
        "blur_strength": 10,
        "blur_passes": 3,
        "blur_noise": 0.01,
        "blur_contrast": 0.65,
        "blur_brightness": 0.6,
        "blur_vibrancy": 0.05,
        "shadow_on": "true",
        "shadow_radius": 35,
        "shadow_opacity": 0.65,
        "shadow_render_power": 4,
        "shadow_offset": "-6 8",
        "inactive_dim": 0.22,
        "opacity_offset": -0.08,
        "opacity_inactive_offset": -0.12,
        "bar_blur": False,
    },
    "bloom": {
        "blur_on": "true",
        "blur_strength": 12,
        "blur_passes": 3,
        "blur_noise": 0.005,
        "blur_contrast": 0.85,
        "blur_brightness": 0.9,
        "blur_vibrancy": 0.4,
        "shadow_on": "true",
        "shadow_radius": 30,
        "shadow_opacity": 0.35,
        "shadow_render_power": 1,
        "shadow_offset": "0 6",
        "inactive_dim": 0.08,
        "opacity_offset": -0.06,
        "opacity_inactive_offset": -0.08,
        "bar_blur": True,
    },
}

# ── Anims: motion style ───────────────────────────────────────────────

ANIMS = {
    "none": {
        "enabled": False,
        "lines": [],
    },
    "subtle": {
        "enabled": True,
        "lines": [
            "bezier = whisper, 0.4, 0.0, 0.6, 1.0",
            "animation = windowsIn, 1, 8, whisper, slide",
            "animation = windowsOut, 1, 8, whisper, slide",
            "animation = windowsMove, 1, 6, whisper, slide",
            "animation = fade, 1, 8, whisper",
            "animation = fadeDim, 1, 8, whisper",
            "animation = workspaces, 1, 8, whisper, slide",
            "animation = border, 1, 10, whisper",
        ],
    },
    "smooth": {
        "enabled": True,
        "lines": [
            "bezier = ease, 0.25, 0.1, 0.25, 1.0",
            "animation = windowsIn, 1, 5, ease, slide",
            "animation = windowsOut, 1, 4, ease, slide",
            "animation = windowsMove, 1, 4, ease, slide",
            "animation = fade, 1, 4, ease",
            "animation = fadeDim, 1, 5, ease",
            "animation = workspaces, 1, 5, ease, slide",
            "animation = border, 1, 6, ease",
            "animation = borderangle, 1, 6, ease",
        ],
    },
    "snappy": {
        "enabled": True,
        "lines": [
            "bezier = snap, 0.15, 1.0, 0.3, 1.0",
            "animation = windowsIn, 1, 2, snap, slide",
            "animation = windowsOut, 1, 2, snap, slide",
            "animation = windowsMove, 1, 2, snap, slide",
            "animation = fade, 1, 2, snap",
            "animation = fadeDim, 1, 2, snap",
            "animation = workspaces, 1, 2, snap, slide",
            "animation = border, 1, 3, snap",
        ],
    },
    "bouncy": {
        "enabled": True,
        "lines": [
            "bezier = spring, 0.0, 1.2, 0.3, 1.0",
            "bezier = springOut, 0.3, -0.3, 0.8, 1.0",
            "animation = windowsIn, 1, 5, spring, popin 60%",
            "animation = windowsOut, 1, 4, springOut, popin 60%",
            "animation = windowsMove, 1, 4, spring, slide",
            "animation = fade, 1, 4, spring",
            "animation = fadeDim, 1, 5, spring",
            "animation = fadeShadow, 1, 4, spring",
            "animation = workspaces, 1, 5, spring, slidefade 50%",
            "animation = border, 1, 6, spring",
        ],
    },
    "dramatic": {
        "enabled": True,
        "lines": [
            "bezier = cinematic, 0.05, 0.9, 0.1, 1.0",
            "bezier = fadeIn, 0.0, 0.0, 0.2, 1.0",
            "animation = windowsIn, 1, 8, cinematic, popin 40%",
            "animation = windowsOut, 1, 6, cinematic, popin 40%",
            "animation = windowsMove, 1, 6, cinematic, slide",
            "animation = fade, 1, 7, fadeIn",
            "animation = fadeDim, 1, 8, fadeIn",
            "animation = fadeShadow, 1, 6, fadeIn",
            "animation = workspaces, 1, 7, cinematic, slidefade 60%",
            "animation = specialWorkspace, 1, 6, cinematic, slidefadevert 40%",
            "animation = border, 1, 8, cinematic",
            "animation = borderangle, 1, 40, cinematic, loop",
        ],
    },
    "glitch": {
        "enabled": True,
        "lines": [
            "bezier = spike, 0.0, 1.6, 0.4, 0.9",
            "bezier = cut, 0.9, 0.0, 1.0, 1.0",
            "animation = windowsIn, 1, 2, spike, popin 85%",
            "animation = windowsOut, 1, 1, cut, popin 85%",
            "animation = windowsMove, 1, 2, spike, slide",
            "animation = fade, 1, 2, cut",
            "animation = fadeDim, 1, 1, cut",
            "animation = fadeShadow, 1, 1, cut",
            "animation = workspaces, 1, 2, spike, slidefade 80%",
            "animation = specialWorkspace, 1, 2, spike, slidefadevert 80%",
            "animation = border, 1, 3, spike",
            "animation = borderangle, 1, 20, spike, loop",
        ],
    },
}

# ── Offset keys applied to theme base values ─────────────────────────

OFFSET_KEYS = {
    "opacity_offset": ("opacity", 0.65, 1.0),
    "opacity_inactive_offset": ("opacity_inactive", 0.55, 1.0),
    "gaps_offset": ("gaps", 0, 30),
    "corner_radius_offset": ("corner_radius", 0, 28),
}

# Texture keys that directly replace theme values
TEXTURE_DIRECT_KEYS = [
    "blur_on", "blur_strength", "shadow_on", "shadow_radius",
    "shadow_opacity", "inactive_dim",
]

# Shape keys that directly replace theme values
SHAPE_DIRECT_KEYS = [
    "border_width",
]

# ── Profile persistence ──────────────────────────────────────────────

def _load_profile_raw():
    try:
        with open(PROFILE_PATH) as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _save_profile_raw(data):
    directory = os.path.dirname(PROFILE_PATH)
    os.makedirs(directory, exist_ok=True)
    data["version"] = 3
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


def profile_shape():
    raw = _load_profile_raw()
    name = raw.get("shape")
    return name if name and name in SHAPES else None


def profile_texture():
    raw = _load_profile_raw()
    name = raw.get("texture")
    return name if name and name in TEXTURES else None


def profile_anim():
    raw = _load_profile_raw()
    name = raw.get("anim")
    return name if name and name in ANIMS else None


def profile():
    """Back-compat: returns texture name (was 'look'/'preset')."""
    raw = _load_profile_raw()
    for key in ("texture", "look", "preset"):
        name = raw.get(key)
        if name and name in TEXTURES:
            return name
    return None


def save_shape(name):
    raw = _load_profile_raw()
    raw["shape"] = name
    raw.pop("preset", None)
    raw.pop("look", None)
    _save_profile_raw(raw)


def save_texture(name):
    raw = _load_profile_raw()
    raw["texture"] = name
    raw.pop("preset", None)
    raw.pop("look", None)
    _save_profile_raw(raw)


def save_anim(name):
    raw = _load_profile_raw()
    raw["anim"] = name
    raw.pop("preset", None)
    raw.pop("look", None)
    _save_profile_raw(raw)


def save(preset_name):
    """Back-compat."""
    raw = _load_profile_raw()
    raw["texture"] = preset_name
    raw.pop("preset", None)
    raw.pop("look", None)
    _save_profile_raw(raw)


# ── Validation / listing ─────────────────────────────────────────────

def validate_preset(name):
    return name in TEXTURES


def validate_shape(name):
    return name in SHAPES


def validate_texture(name):
    return name in TEXTURES


def validate_anim(name):
    return name in ANIMS


def list_presets():
    return list(TEXTURES.keys())


def list_shapes():
    return list(SHAPES.keys())


def list_textures():
    return list(TEXTURES.keys())


def list_anims():
    return list(ANIMS.keys())


# ── Style resolution ─────────────────────────────────────────────────

def resolve(style, shape_name=None, texture_name=None):
    """Merge shape and texture overrides onto the theme's base style dict.
    Back-compat: if called with a single string second arg and no third,
    treat it as texture_name (old 'preset' interface)."""
    if isinstance(shape_name, str) and texture_name is None:
        if shape_name in TEXTURES:
            texture_name = shape_name
            shape_name = None
        elif shape_name not in SHAPES:
            return dict(style)

    merged = dict(style)

    if shape_name and shape_name in SHAPES:
        shape = SHAPES[shape_name]
        for key in SHAPE_DIRECT_KEYS:
            if key in shape:
                merged[key] = shape[key]
        if "rounding_power" in shape:
            merged["rounding_power"] = shape["rounding_power"]
        for offset_key, (target, lo, hi) in OFFSET_KEYS.items():
            if offset_key in shape:
                base = float(merged.get(target, 10 if "radius" in target else 8))
                merged[target] = round(max(lo, min(hi, base + shape[offset_key])), 2)

    if texture_name and texture_name in TEXTURES:
        texture = TEXTURES[texture_name]
        for key in TEXTURE_DIRECT_KEYS:
            if key in texture:
                merged[key] = texture[key]
        for extra in ("blur_passes", "blur_noise", "blur_contrast",
                       "blur_brightness", "blur_vibrancy",
                       "shadow_render_power", "shadow_offset", "bar_blur"):
            if extra in texture:
                merged[extra] = texture[extra]
        for offset_key, (target, lo, hi) in OFFSET_KEYS.items():
            if offset_key in texture:
                base = float(merged.get(target, 1.0 if "opacity" in target else 8))
                merged[target] = round(max(lo, min(hi, base + texture[offset_key])), 2)

    return merged


# ── Animation rendering ──────────────────────────────────────────────

def render_animations(anim_name):
    if anim_name is None:
        return []
    if anim_name not in ANIMS:
        return []
    anim = ANIMS[anim_name]
    if not anim["enabled"]:
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
    for anim_line in anim["lines"]:
        lines.append(f"    {anim_line}")
    lines.append("}")
    return lines
