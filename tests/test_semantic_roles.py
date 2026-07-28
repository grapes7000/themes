"""Tests for the semantic color role system."""
import importlib.machinery
import importlib.util
import json
import glob
import os
import re
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

_theme_path = os.path.join(os.path.dirname(__file__), "..", "bin", "theme")
_spec = importlib.util.spec_from_loader(
    "theme_main",
    importlib.machinery.SourceFileLoader("theme_main", _theme_path),
)
theme = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(theme)


THEME_DIR = os.path.join(os.path.dirname(__file__), "..", "themes")
CORE_ROLES = {"bg", "bg_alt", "text", "text_dim", "accent", "accent2",
               "urgent", "focus", "border_normal"}
SEMANTIC_ROLES = {"surface_0", "surface_1", "surface_2", "overlay", "hover",
                   "selected", "border_subtle", "border_strong", "success",
                   "warning", "info", "disabled", "shadow", "on_accent",
                   "on_urgent"}
ALL_ROLES = CORE_ROLES | SEMANTIC_ROLES
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


# ── Color helper tests ───────────────────────────────────────────────

class TestColorHelpers:
    def test_hex_to_rgb(self):
        assert theme.hex_to_rgb("#ff0000") == (255, 0, 0)
        assert theme.hex_to_rgb("#00ff00") == (0, 255, 0)
        assert theme.hex_to_rgb("#1e1e2e") == (30, 30, 46)

    def test_rgb_to_hex(self):
        assert theme.rgb_to_hex(255, 0, 0) == "#ff0000"
        assert theme.rgb_to_hex(0, 255, 0) == "#00ff00"
        assert theme.rgb_to_hex(30, 30, 46) == "#1e1e2e"

    def test_rgb_to_hex_clamps(self):
        assert theme.rgb_to_hex(-10, 300, 128) == "#00ff80"

    def test_blend_endpoints(self):
        assert theme.blend("#000000", "#ffffff", 0.0) == "#000000"
        assert theme.blend("#000000", "#ffffff", 1.0) == "#ffffff"

    def test_blend_midpoint(self):
        result = theme.blend("#000000", "#ffffff", 0.5)
        r, g, b = theme.hex_to_rgb(result)
        assert 126 <= r <= 128
        assert r == g == b

    def test_contrast_ratio_black_white(self):
        ratio = theme.contrast_ratio("#000000", "#ffffff")
        assert abs(ratio - 21.0) < 0.1

    def test_contrast_ratio_same_color(self):
        ratio = theme.contrast_ratio("#abcdef", "#abcdef")
        assert abs(ratio - 1.0) < 0.001

    def test_best_contrast(self):
        result = theme.best_contrast("#000000", ["#111111", "#ffffff"])
        assert result == "#ffffff"
        result = theme.best_contrast("#ffffff", ["#000000", "#eeeeee"])
        assert result == "#000000"


# ── Semantic resolver tests ──────────────────────────────────────────

class TestResolveSemanticRoles:
    @pytest.fixture
    def minimal_roles(self):
        return {
            "bg": "#1e1e2e", "bg_alt": "#313244", "text": "#cdd6f4",
            "text_dim": "#a6adc8", "accent": "#cba6f7", "accent2": "#89b4fa",
            "urgent": "#f38ba8", "focus": "#cba6f7", "border_normal": "#45475a",
            "ansi_green": "#a6e3a1", "ansi_yellow": "#f9e2af",
            "ansi_blue": "#89b4fa",
        }

    def test_all_semantic_roles_present(self, minimal_roles):
        resolved = theme.resolve_semantic_roles(minimal_roles)
        for role in SEMANTIC_ROLES:
            assert role in resolved, f"Missing role: {role}"

    def test_all_values_are_valid_hex(self, minimal_roles):
        resolved = theme.resolve_semantic_roles(minimal_roles)
        for role in ALL_ROLES:
            if role in resolved:
                assert HEX_RE.match(resolved[role]), \
                    f"{role} = {resolved[role]} is not valid hex"

    def test_preserves_existing_core_roles(self, minimal_roles):
        resolved = theme.resolve_semantic_roles(minimal_roles)
        for role in CORE_ROLES:
            assert resolved[role] == minimal_roles[role]

    def test_preserves_explicit_semantic_override(self, minimal_roles):
        minimal_roles["surface_0"] = "#aabbcc"
        resolved = theme.resolve_semantic_roles(minimal_roles)
        assert resolved["surface_0"] == "#aabbcc"

    def test_success_uses_ansi_green(self, minimal_roles):
        resolved = theme.resolve_semantic_roles(minimal_roles)
        assert resolved["success"] == "#a6e3a1"

    def test_warning_uses_ansi_yellow(self, minimal_roles):
        resolved = theme.resolve_semantic_roles(minimal_roles)
        assert resolved["warning"] == "#f9e2af"

    def test_info_uses_ansi_blue(self, minimal_roles):
        resolved = theme.resolve_semantic_roles(minimal_roles)
        assert resolved["info"] == "#89b4fa"

    def test_on_accent_has_good_contrast(self, minimal_roles):
        resolved = theme.resolve_semantic_roles(minimal_roles)
        ratio = theme.contrast_ratio(resolved["accent"], resolved["on_accent"])
        # best_contrast picks the highest-contrast candidate from [bg, text];
        # 2.0 is a floor sanity check, not a WCAG guarantee — the actual ratio
        # depends on theme palette and may exceed WCAG AA (4.5) for most themes.
        assert ratio > 2.0

    def test_on_urgent_has_good_contrast(self, minimal_roles):
        resolved = theme.resolve_semantic_roles(minimal_roles)
        ratio = theme.contrast_ratio(resolved["urgent"], resolved["on_urgent"])
        assert ratio > 2.0

    def test_does_not_mutate_input(self, minimal_roles):
        snapshot = dict(minimal_roles)
        theme.resolve_semantic_roles(minimal_roles)
        assert minimal_roles == snapshot

    def test_success_fallback_without_ansi_green(self, minimal_roles):
        del minimal_roles["ansi_green"]
        resolved = theme.resolve_semantic_roles(minimal_roles)
        assert resolved["success"] == minimal_roles["accent2"]

    def test_warning_fallback_without_ansi_yellow(self, minimal_roles):
        del minimal_roles["ansi_yellow"]
        resolved = theme.resolve_semantic_roles(minimal_roles)
        assert resolved["warning"] == minimal_roles["accent2"]

    def test_info_fallback_without_ansi_blue(self, minimal_roles):
        del minimal_roles["ansi_blue"]
        resolved = theme.resolve_semantic_roles(minimal_roles)
        assert resolved["info"] == minimal_roles["accent2"]

    def test_fallbacks_with_no_ansi_status_colors(self, minimal_roles):
        for k in ("ansi_green", "ansi_yellow", "ansi_blue"):
            del minimal_roles[k]
        resolved = theme.resolve_semantic_roles(minimal_roles)
        for role in ("success", "warning", "info"):
            assert role in resolved
            assert resolved[role] == minimal_roles["accent2"]


# ── Backward compatibility: all 36 themes ───────────────────────────

def all_theme_paths():
    return sorted(glob.glob(os.path.join(THEME_DIR, "*.json")))


@pytest.mark.parametrize("theme_path", all_theme_paths(),
                         ids=lambda p: os.path.basename(p))
class TestAllThemesResolve:
    def test_resolves_without_error(self, theme_path):
        t = json.load(open(theme_path))
        roles = t["roles"]
        resolved = theme.resolve_semantic_roles(roles)
        assert isinstance(resolved, dict)

    def test_all_roles_valid_hex(self, theme_path):
        t = json.load(open(theme_path))
        resolved = theme.resolve_semantic_roles(t["roles"])
        for role in ALL_ROLES:
            if role in resolved:
                assert HEX_RE.match(resolved[role]), \
                    f"{os.path.basename(theme_path)}: {role} = {resolved[role]}"

    def test_core_roles_unchanged(self, theme_path):
        t = json.load(open(theme_path))
        original = dict(t["roles"])
        resolved = theme.resolve_semantic_roles(t["roles"])
        for role in CORE_ROLES:
            if role in original:
                assert resolved[role] == original[role], \
                    f"{os.path.basename(theme_path)}: {role} changed"

    def test_semantic_roles_all_present(self, theme_path):
        t = json.load(open(theme_path))
        resolved = theme.resolve_semantic_roles(t["roles"])
        for role in SEMANTIC_ROLES:
            assert role in resolved, \
                f"{os.path.basename(theme_path)}: missing {role}"
