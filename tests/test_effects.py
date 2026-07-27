"""Tests for the effects-profile system (theme_effects module)."""

import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
import theme_effects


SAMPLE_STYLE = {
    "corner_radius": 14,
    "opacity": 0.94,
    "opacity_inactive": 0.86,
    "inactive_dim": 0.1,
    "blur_on": "true",
    "blur_strength": 9,
    "shadow_on": "true",
    "shadow_radius": 22,
    "shadow_opacity": 0.45,
    "shadow_offset": "0 -12",
    "gaps": 9,
    "border_width": 2,
}

SAMPLE_ROLES = {
    "bg": "#1e1e2e",
    "bg_alt": "#181825",
    "text": "#cdd6f4",
    "text_dim": "#a6adc8",
    "focus": "#cba6f7",
    "border_normal": "#313244",
    "accent": "#cba6f7",
    "accent2": "#89b4fa",
    "urgent": "#f38ba8",
    "sel_bg": "#cba6f7",
    "sel_fg": "#1e1e2e",
    "cursor": "#cba6f7",
}


# ── Axis names ────────────────────────────────────────────────────────

class TestAxisNames:
    def test_shapes_exist(self):
        assert set(theme_effects.list_shapes()) == {"sharp", "rounded", "pillowy", "boxy"}

    def test_textures_exist(self):
        assert set(theme_effects.list_textures()) == {"clear", "frosted", "glaze", "haze", "bloom"}

    def test_anims_exist(self):
        assert set(theme_effects.list_anims()) == {"none", "subtle", "smooth", "snappy", "bouncy", "dramatic", "glitch"}

    def test_validate_shape(self):
        for name in theme_effects.list_shapes():
            assert theme_effects.validate_shape(name) is True
        assert theme_effects.validate_shape("nonexistent") is False

    def test_validate_texture(self):
        for name in theme_effects.list_textures():
            assert theme_effects.validate_texture(name) is True
        assert theme_effects.validate_texture("nonexistent") is False

    def test_validate_anim(self):
        for name in theme_effects.list_anims():
            assert theme_effects.validate_anim(name) is True
        assert theme_effects.validate_anim("nonexistent") is False


class TestBackCompatNames:
    def test_list_presets_returns_textures(self):
        assert set(theme_effects.list_presets()) == set(theme_effects.list_textures())

    def test_validate_preset_matches_textures(self):
        for name in theme_effects.list_textures():
            assert theme_effects.validate_preset(name) is True
        assert theme_effects.validate_preset("nonexistent") is False
        assert theme_effects.validate_preset("") is False
        assert theme_effects.validate_preset(None) is False


# ── Resolve ───────────────────────────────────────────────────────────

class TestResolve:
    def test_none_passthrough(self):
        result = theme_effects.resolve(SAMPLE_STYLE, None)
        assert result == SAMPLE_STYLE

    def test_none_returns_copy(self):
        result = theme_effects.resolve(SAMPLE_STYLE, None)
        assert result is not SAMPLE_STYLE

    def test_no_mutation(self):
        original = dict(SAMPLE_STYLE)
        theme_effects.resolve(SAMPLE_STYLE, "sharp", "frosted")
        assert SAMPLE_STYLE == original

    def test_texture_merges_style_keys(self):
        result = theme_effects.resolve(SAMPLE_STYLE, None, "clear")
        assert result["blur_on"] == "false"
        assert result["shadow_on"] == "false"
        assert result["inactive_dim"] == 0

    def test_shape_merges_border(self):
        result = theme_effects.resolve(SAMPLE_STYLE, "sharp", None)
        assert result["border_width"] == 1

    def test_preserves_non_overridden_keys(self):
        result = theme_effects.resolve(SAMPLE_STYLE, "sharp", None)
        assert result["blur_on"] == "true"
        assert result["shadow_radius"] == 22

    def test_each_texture_resolves(self):
        for name in theme_effects.list_textures():
            result = theme_effects.resolve(SAMPLE_STYLE, None, name)
            assert isinstance(result, dict)
            assert "blur_on" in result

    def test_each_shape_resolves(self):
        for name in theme_effects.list_shapes():
            result = theme_effects.resolve(SAMPLE_STYLE, name, None)
            assert isinstance(result, dict)

    def test_unknown_shape_passthrough(self):
        result = theme_effects.resolve(SAMPLE_STYLE, "bad", None)
        assert result == SAMPLE_STYLE

    def test_back_compat_single_texture_arg(self):
        result = theme_effects.resolve(SAMPLE_STYLE, "clear")
        assert result["blur_on"] == "false"


# ── Render animations ────────────────────────────────────────────────

class TestRenderAnimations:
    def test_none_returns_empty(self):
        result = theme_effects.render_animations(None)
        assert result == []

    def test_anim_none_disabled(self):
        lines = theme_effects.render_animations("none")
        text = "\n".join(lines)
        assert "enabled = false" in text

    def test_smooth_has_animations(self):
        lines = theme_effects.render_animations("smooth")
        text = "\n".join(lines)
        assert "enabled = true" in text
        assert "bezier" in text
        assert "windowsIn" in text
        assert "windowsOut" in text
        assert "workspaces" in text

    def test_subtle_has_animations(self):
        lines = theme_effects.render_animations("subtle")
        text = "\n".join(lines)
        assert "enabled = true" in text
        assert "windowsIn" in text

    def test_bouncy_has_popin(self):
        lines = theme_effects.render_animations("bouncy")
        text = "\n".join(lines)
        assert "popin" in text

    def test_each_anim_valid_syntax(self):
        for name in theme_effects.list_anims():
            lines = theme_effects.render_animations(name)
            text = "\n".join(lines)
            assert "animations {" in text
            assert text.rstrip().endswith("}")

    def test_unknown_anim_returns_empty(self):
        result = theme_effects.render_animations("bad")
        assert result == []


# ── Profile persistence ──────────────────────────────────────────────

class TestProfileRoundtrip:
    def test_save_and_load_texture(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        theme_effects.save_texture("frosted")
        assert theme_effects.profile_texture() == "frosted"

    def test_save_and_load_shape(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        theme_effects.save_shape("pillowy")
        assert theme_effects.profile_shape() == "pillowy"

    def test_save_and_load_anim(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        theme_effects.save_anim("bouncy")
        assert theme_effects.profile_anim() == "bouncy"

    def test_save_none_clears(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        theme_effects.save_texture("frosted")
        theme_effects.save_texture(None)
        assert theme_effects.profile_texture() is None

    def test_back_compat_save_and_profile(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        theme_effects.save("frosted")
        assert theme_effects.profile() == "frosted"

    def test_missing_file(self, tmp_path, monkeypatch):
        path = str(tmp_path / "nonexistent" / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        assert theme_effects.profile() is None
        assert theme_effects.profile_shape() is None
        assert theme_effects.profile_texture() is None
        assert theme_effects.profile_anim() is None

    def test_corrupt_file(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        with open(path, "w") as f:
            f.write("not json{{{")
        assert theme_effects.profile() is None

    def test_invalid_name_in_file(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        with open(path, "w") as f:
            json.dump({"version": 3, "texture": "nonexistent"}, f)
        assert theme_effects.profile_texture() is None

    def test_axes_independent(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        theme_effects.save_shape("sharp")
        theme_effects.save_texture("bloom")
        theme_effects.save_anim("glitch")
        assert theme_effects.profile_shape() == "sharp"
        assert theme_effects.profile_texture() == "bloom"
        assert theme_effects.profile_anim() == "glitch"


# ── gen_hypr integration ─────────────────────────────────────────────

class TestGenHyprIntegration:
    """Test that gen_hypr produces correct output with and without effects."""

    @staticmethod
    def _load_theme_module():
        import importlib.util
        theme_path = os.path.join(os.path.dirname(__file__), "..", "bin", "theme")
        loader = importlib.util.spec_from_loader(
            "theme_main",
            importlib.machinery.SourceFileLoader("theme_main", theme_path),
        )
        mod = importlib.util.module_from_spec(loader)
        loader.loader.exec_module(mod)
        return mod

    def _gen_hypr_output(self, roles, style,
                         shape_name=None, texture_name=None, anim_name=None):
        mod = self._load_theme_module()
        captured = {}

        def fake_write(path, text):
            captured["text"] = text

        original_write = mod.write
        mod.write = fake_write
        try:
            mod.gen_hypr(roles, style, shape_name, texture_name, anim_name)
        finally:
            mod.write = original_write
        return captured.get("text", "")

    def test_no_effects(self):
        output = self._gen_hypr_output(SAMPLE_ROLES, SAMPLE_STYLE)
        assert "animations {" not in output
        assert "col.active_border" in output
        assert "col.inactive_border" in output
        assert "dim_inactive" in output

    def test_with_smooth_anim(self):
        output = self._gen_hypr_output(SAMPLE_ROLES, SAMPLE_STYLE,
                                       anim_name="smooth")
        assert "animations {" in output
        assert "enabled = true" in output
        assert "windowsIn" in output

    def test_with_none_anim(self):
        output = self._gen_hypr_output(SAMPLE_ROLES, SAMPLE_STYLE,
                                       anim_name="none")
        assert "animations {" in output
        assert "enabled = false" in output

    def test_with_texture(self):
        output = self._gen_hypr_output(SAMPLE_ROLES, SAMPLE_STYLE,
                                       texture_name="frosted")
        assert "blur" in output

    def test_semantic_roles_in_output(self):
        output = self._gen_hypr_output(SAMPLE_ROLES, SAMPLE_STYLE,
                                       anim_name="smooth")
        assert "cba6f7" in output
        assert "89b4fa" in output
        assert "313244" in output

    def test_no_hardcoded_colors(self):
        alt_roles = dict(SAMPLE_ROLES)
        alt_roles["focus"] = "#ff0000"
        alt_roles["accent2"] = "#00ff00"
        alt_roles["border_normal"] = "#0000ff"
        output = self._gen_hypr_output(alt_roles, SAMPLE_STYLE,
                                       anim_name="smooth")
        assert "ff0000" in output
        assert "00ff00" in output
        assert "0000ff" in output
