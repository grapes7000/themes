"""Tests for the desktop homepage overlay (theme_homepage module)."""

import importlib.machinery
import importlib.util
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
import theme_homepage


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
    "gaps": 9,
    "border_width": 2,
}

ALT_ROLES = {
    "bg": "#282c34",
    "bg_alt": "#21252b",
    "text": "#abb2bf",
    "text_dim": "#5c6370",
    "focus": "#61afef",
    "border_normal": "#3e4452",
    "accent": "#61afef",
    "accent2": "#c678dd",
    "urgent": "#e06c75",
}


class TestProfile:
    def test_defaults_on_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(theme_homepage, "PROFILE_PATH",
                            str(tmp_path / "nope" / "homepage.json"))
        hp = theme_homepage.profile()
        assert hp["enabled"] is False
        assert hp["alignment"] == "left"
        assert hp["version"] == 1

    def test_roundtrip(self, tmp_path, monkeypatch):
        path = str(tmp_path / "homepage.json")
        monkeypatch.setattr(theme_homepage, "PROFILE_PATH", path)
        theme_homepage.save({"version": 1, "enabled": True, "alignment": "right"})
        hp = theme_homepage.profile()
        assert hp["enabled"] is True
        assert hp["alignment"] == "right"

    def test_corrupt_file_returns_defaults(self, tmp_path, monkeypatch):
        path = str(tmp_path / "homepage.json")
        monkeypatch.setattr(theme_homepage, "PROFILE_PATH", path)
        with open(path, "w") as f:
            f.write("{broken json")
        hp = theme_homepage.profile()
        assert hp["alignment"] == "left"

    def test_wrong_type_ignored(self, tmp_path, monkeypatch):
        path = str(tmp_path / "homepage.json")
        monkeypatch.setattr(theme_homepage, "PROFILE_PATH", path)
        with open(path, "w") as f:
            json.dump({"version": 1, "enabled": "yes", "alignment": 42}, f)
        hp = theme_homepage.profile()
        assert hp["enabled"] is False
        assert hp["alignment"] == "left"


class TestRenderScss:
    def test_has_all_roles(self):
        scss = theme_homepage.render_scss(SAMPLE_ROLES, SAMPLE_STYLE)
        for role in ["bg", "bg-alt", "text", "text-dim", "accent", "accent2",
                      "urgent", "focus", "border-normal"]:
            assert f"${role}:" in scss

    def test_no_hardcoded_colors(self):
        scss1 = theme_homepage.render_scss(SAMPLE_ROLES, SAMPLE_STYLE)
        scss2 = theme_homepage.render_scss(ALT_ROLES, SAMPLE_STYLE)
        assert scss1 != scss2
        assert "#1e1e2e" in scss1
        assert "#282c34" in scss2

    def test_effects_opacity_minimal(self):
        scss = theme_homepage.render_scss(SAMPLE_ROLES, SAMPLE_STYLE, "minimal")
        assert "0.85" in scss

    def test_effects_opacity_cyber(self):
        scss = theme_homepage.render_scss(SAMPLE_ROLES, SAMPLE_STYLE, "cyber")
        assert "0.6" in scss

    def test_corner_radius_from_style(self):
        scss = theme_homepage.render_scss(SAMPLE_ROLES, SAMPLE_STYLE)
        assert "14px" in scss

    def test_auto_generated_header(self):
        scss = theme_homepage.render_scss(SAMPLE_ROLES, SAMPLE_STYLE)
        assert "AUTO-GENERATED" in scss


class TestRenderYuck:
    def test_left_alignment(self):
        yuck = theme_homepage.render_yuck({"alignment": "left"})
        assert 'anchor "top left"' in yuck

    def test_right_alignment(self):
        yuck = theme_homepage.render_yuck({"alignment": "right"})
        assert 'anchor "top right"' in yuck

    def test_five_widgets(self):
        yuck = theme_homepage.render_yuck({"alignment": "left"})
        assert "(defwidget clock" in yuck
        assert "(defwidget theme-info" in yuck
        assert "(defwidget workspaces" in yuck
        assert "(defwidget sysinfo-widget" in yuck
        assert "(defwidget media-widget" in yuck

    def test_media_conditional_visibility(self):
        yuck = theme_homepage.render_yuck({"alignment": "left"})
        assert "visible" in yuck
        assert "playing" in yuck

    def test_theme_name_in_output(self):
        yuck = theme_homepage.render_yuck({"alignment": "left"}, theme_name="catppuccin_mocha")
        assert "catppuccin_mocha" in yuck

    def test_effects_label(self):
        yuck = theme_homepage.render_yuck({"alignment": "left"}, effects_preset="polished")
        assert "polished" in yuck

    def test_effects_none_label(self):
        yuck = theme_homepage.render_yuck({"alignment": "left"}, effects_preset=None)
        assert "none" in yuck

    def test_auto_generated_header(self):
        yuck = theme_homepage.render_yuck({"alignment": "left"})
        assert "AUTO-GENERATED" in yuck


class TestRenderScripts:
    def test_returns_three_scripts(self):
        scripts = theme_homepage.render_scripts()
        assert set(scripts.keys()) == {"sysinfo.sh", "media.sh", "workspaces.sh"}

    def test_all_have_shebang(self):
        for name, content in theme_homepage.render_scripts().items():
            assert content.startswith("#!/usr/bin/env bash"), f"{name} missing shebang"

    def test_sysinfo_reads_proc(self):
        scripts = theme_homepage.render_scripts()
        assert "/proc/stat" in scripts["sysinfo.sh"]
        assert "/proc/meminfo" in scripts["sysinfo.sh"]
        assert "/proc/uptime" in scripts["sysinfo.sh"]

    def test_media_handles_missing_playerctl(self):
        scripts = theme_homepage.render_scripts()
        assert "command -v playerctl" in scripts["media.sh"]
        assert '"playing":false' in scripts["media.sh"]

    def test_workspaces_handles_missing_hyprctl(self):
        scripts = theme_homepage.render_scripts()
        assert "command -v hyprctl" in scripts["workspaces.sh"]

    def test_scripts_output_json(self):
        scripts = theme_homepage.render_scripts()
        for name in ("sysinfo.sh", "media.sh"):
            assert "printf" in scripts[name] or "echo" in scripts[name]


class TestPidfile:
    def test_not_running_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(theme_homepage, "PIDFILE",
                            str(tmp_path / "nope.pid"))
        assert theme_homepage.is_running() is False

    def test_not_running_when_stale(self, tmp_path, monkeypatch):
        pidfile = str(tmp_path / "stale.pid")
        monkeypatch.setattr(theme_homepage, "PIDFILE", pidfile)
        with open(pidfile, "w") as f:
            f.write("99999999\n")
        assert theme_homepage.is_running() is False

    def test_not_running_when_corrupt(self, tmp_path, monkeypatch):
        pidfile = str(tmp_path / "bad.pid")
        monkeypatch.setattr(theme_homepage, "PIDFILE", pidfile)
        with open(pidfile, "w") as f:
            f.write("not-a-pid\n")
        assert theme_homepage.is_running() is False


class TestGenHomepageIntegration:
    @staticmethod
    def _load_theme_module():
        theme_path = os.path.join(os.path.dirname(__file__), "..", "bin", "theme")
        loader = importlib.util.spec_from_loader(
            "theme_main",
            importlib.machinery.SourceFileLoader("theme_main", theme_path),
        )
        mod = importlib.util.module_from_spec(loader)
        loader.loader.exec_module(mod)
        return mod

    def test_gen_homepage_writes_files(self, tmp_path):
        mod = self._load_theme_module()
        written = {}

        def fake_write(path, text):
            written[path] = text

        orig_write = mod.write
        orig_chmod = os.chmod
        mod.write = fake_write
        os.chmod = lambda *a, **kw: None
        try:
            mod.gen_homepage(SAMPLE_ROLES, SAMPLE_STYLE, "testtheme", "polished")
        finally:
            mod.write = orig_write
            os.chmod = orig_chmod

        paths = list(written.keys())
        basenames = [os.path.basename(p) for p in paths]
        assert "eww.scss" in basenames
        assert "eww.yuck" in basenames
        assert "sysinfo.sh" in basenames
        assert "media.sh" in basenames
        assert "workspaces.sh" in basenames

    def test_gen_homepage_scss_has_theme_colors(self, tmp_path):
        mod = self._load_theme_module()
        written = {}

        def fake_write(path, text):
            written[path] = text

        orig_write = mod.write
        orig_chmod = os.chmod
        mod.write = fake_write
        os.chmod = lambda *a, **kw: None
        try:
            mod.gen_homepage(SAMPLE_ROLES, SAMPLE_STYLE, "testtheme")
        finally:
            mod.write = orig_write
            os.chmod = orig_chmod

        scss_path = [p for p in written if p.endswith("eww.scss")][0]
        scss = written[scss_path]
        assert "#1e1e2e" in scss
        assert "#cba6f7" in scss
