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
    "shadow_offset": -12,
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


class TestPresetNames:
    def test_all_four_exist(self):
        names = theme_effects.list_presets()
        assert set(names) == {"minimal", "calm", "polished", "cyber"}

    def test_validate_valid(self):
        for name in ("minimal", "calm", "polished", "cyber"):
            assert theme_effects.validate_preset(name) is True

    def test_validate_invalid(self):
        assert theme_effects.validate_preset("nonexistent") is False
        assert theme_effects.validate_preset("") is False
        assert theme_effects.validate_preset(None) is False


class TestResolve:
    def test_none_passthrough(self):
        result = theme_effects.resolve(SAMPLE_STYLE, None)
        assert result == SAMPLE_STYLE

    def test_none_returns_copy(self):
        result = theme_effects.resolve(SAMPLE_STYLE, None)
        assert result is not SAMPLE_STYLE

    def test_no_mutation(self):
        original = dict(SAMPLE_STYLE)
        theme_effects.resolve(SAMPLE_STYLE, "cyber")
        assert SAMPLE_STYLE == original

    def test_merges_style_keys(self):
        result = theme_effects.resolve(SAMPLE_STYLE, "minimal")
        assert result["blur_on"] == "false"
        assert result["shadow_on"] == "false"
        assert result["inactive_dim"] == 0
        assert result["border_width"] == 1

    def test_preserves_non_overridden_keys(self):
        result = theme_effects.resolve(SAMPLE_STYLE, "minimal")
        assert result["corner_radius"] == 14
        assert result["opacity"] == 0.94
        assert result["gaps"] == 9

    def test_each_preset_resolves(self):
        for name in theme_effects.list_presets():
            result = theme_effects.resolve(SAMPLE_STYLE, name)
            assert isinstance(result, dict)
            assert "blur_on" in result

    def test_invalid_preset_raises(self):
        with pytest.raises(ValueError, match="unknown effects preset"):
            theme_effects.resolve(SAMPLE_STYLE, "bad")


class TestRenderAnimations:
    def test_none_returns_empty(self):
        result = theme_effects.render_animations(None)
        assert result == []

    def test_minimal_disabled(self):
        lines = theme_effects.render_animations("minimal")
        text = "\n".join(lines)
        assert "enabled = false" in text

    def test_polished_has_animations(self):
        lines = theme_effects.render_animations("polished")
        text = "\n".join(lines)
        assert "enabled = true" in text
        assert "bezier" in text
        assert "windowsIn" in text
        assert "windowsOut" in text
        assert "workspaces" in text

    def test_calm_has_animations(self):
        lines = theme_effects.render_animations("calm")
        text = "\n".join(lines)
        assert "enabled = true" in text
        assert "windowsIn" in text

    def test_cyber_has_popin(self):
        lines = theme_effects.render_animations("cyber")
        text = "\n".join(lines)
        assert "popin" in text

    def test_each_preset_valid_syntax(self):
        for name in theme_effects.list_presets():
            lines = theme_effects.render_animations(name)
            text = "\n".join(lines)
            assert "animations {" in text
            assert text.rstrip().endswith("}")

    def test_invalid_preset_raises(self):
        with pytest.raises(ValueError, match="unknown effects preset"):
            theme_effects.render_animations("bad")


class TestProfileRoundtrip:
    def test_save_and_load(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)

        theme_effects.save("polished")
        assert theme_effects.profile() == "polished"

    def test_save_none(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)

        theme_effects.save("cyber")
        theme_effects.save(None)
        assert theme_effects.profile() is None

    def test_missing_file(self, tmp_path, monkeypatch):
        path = str(tmp_path / "nonexistent" / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        assert theme_effects.profile() is None

    def test_corrupt_file(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        with open(path, "w") as f:
            f.write("not json{{{")
        assert theme_effects.profile() is None

    def test_invalid_preset_in_file(self, tmp_path, monkeypatch):
        path = str(tmp_path / "effects.json")
        monkeypatch.setattr(theme_effects, "PROFILE_PATH", path)
        with open(path, "w") as f:
            json.dump({"version": 1, "preset": "nonexistent"}, f)
        assert theme_effects.profile() is None

    def test_save_invalid_raises(self):
        with pytest.raises(ValueError):
            theme_effects.save("bad_preset")


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

    def _gen_hypr_output(self, roles, style, effects_preset=None):
        mod = self._load_theme_module()
        captured = {}

        def fake_write(path, text):
            captured["text"] = text

        original_write = mod.write
        mod.write = fake_write
        try:
            mod.gen_hypr(roles, style, effects_preset)
        finally:
            mod.write = original_write
        return captured.get("text", "")

    def test_backward_compat_no_preset(self):
        output = self._gen_hypr_output(SAMPLE_ROLES, SAMPLE_STYLE, None)
        assert "animations {" not in output
        assert "col.active_border" in output
        assert "col.inactive_border" in output
        assert "dim_inactive" in output

    def test_with_polished_preset(self):
        output = self._gen_hypr_output(SAMPLE_ROLES, SAMPLE_STYLE, "polished")
        assert "animations {" in output
        assert "enabled = true" in output
        assert "windowsIn" in output

    def test_with_minimal_preset(self):
        output = self._gen_hypr_output(SAMPLE_ROLES, SAMPLE_STYLE, "minimal")
        assert "animations {" in output
        assert "enabled = false" in output

    def test_semantic_roles_in_output(self):
        output = self._gen_hypr_output(SAMPLE_ROLES, SAMPLE_STYLE, "polished")
        assert "cba6f7" in output  # focus role in active border
        assert "89b4fa" in output  # accent2 role in active border
        assert "313244" in output  # border_normal in inactive border

    def test_no_hardcoded_colors(self):
        alt_roles = dict(SAMPLE_ROLES)
        alt_roles["focus"] = "#ff0000"
        alt_roles["accent2"] = "#00ff00"
        alt_roles["border_normal"] = "#0000ff"
        output = self._gen_hypr_output(alt_roles, SAMPLE_STYLE, "polished")
        assert "ff0000" in output
        assert "00ff00" in output
        assert "0000ff" in output
