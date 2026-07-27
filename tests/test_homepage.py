"""Focused tests for the Eww homepage runtime."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
import theme_homepage

ROLES = {
    "bg": "#1e1e2e", "bg_alt": "#181825", "text": "#cdd6f4",
    "text_dim": "#a6adc8", "accent": "#cba6f7", "accent2": "#89b4fa",
    "border_normal": "#313244",
}
STYLE = {"corner_radius": 14}


def test_profile_roundtrip(tmp_path, monkeypatch):
    path = tmp_path / "homepage.json"
    monkeypatch.setattr(theme_homepage, "PROFILE_PATH", path)
    theme_homepage.save({"enabled": True, "alignment": "right"})
    assert theme_homepage.profile()["enabled"] is True
    assert theme_homepage.profile()["alignment"] == "right"


def test_invalid_alignment_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(theme_homepage, "PROFILE_PATH", tmp_path / "homepage.json")
    with pytest.raises(ValueError):
        theme_homepage.save({"enabled": True, "alignment": "sideways"})


def test_semantic_scss_and_generated_warning():
    scss = theme_homepage.render_scss(ROLES, STYLE, "polished")
    assert "AUTO-GENERATED" in scss
    assert "#1e1e2e" in scss
    assert "#cba6f7" in scss
    assert "14px" in scss


def test_workspace_is_dynamic_and_clickable():
    yuck = theme_homepage.render_yuck({"alignment": "left"})
    assert "workspace-state" in yuck
    assert "'.active'" in yuck
    assert "switch-workspace.py" in yuck
    assert "ws == 1" not in yuck


def test_overlay_does_not_claim_full_screen_height():
    yuck = theme_homepage.render_yuck({"alignment": "right"})
    assert 'anchor "top right"' in yuck
    assert ':height "100%"' not in yuck


def test_generated_labels_are_escaped():
    yuck = theme_homepage.render_yuck({"alignment": "left"}, 'bad"\nname', 'calm"')
    assert 'bad\\" name' in yuck
    assert 'calm\\"' in yuck


def test_helpers_are_python_and_json_safe():
    scripts = theme_homepage.render_scripts()
    assert set(scripts) == {"sysinfo.py", "media.py", "workspaces.py", "switch-workspace.py"}
    assert all(value.startswith("#!/usr/bin/env python3") for value in scripts.values())
    assert "json.dumps" in scripts["media.py"]
    assert "re.fullmatch" in scripts["switch-workspace.py"]
    assert "shell=True" not in "".join(scripts.values())


def test_cpu_uses_delta_sample():
    script = theme_homepage.render_scripts()["sysinfo.py"]
    assert "delta_total" in script
    assert "delta_idle" in script
    assert "theme-homepage-cpu.json" in script


def test_missing_pid_is_not_running(tmp_path, monkeypatch):
    monkeypatch.setattr(theme_homepage, "PIDFILE", tmp_path / "missing.pid")
    assert theme_homepage.is_running() is False


def test_unrelated_pid_is_never_treated_as_homepage(tmp_path, monkeypatch):
    pidfile = tmp_path / "homepage.pid"
    pidfile.write_text(str(os.getpid()))
    monkeypatch.setattr(theme_homepage, "PIDFILE", pidfile)
    monkeypatch.setattr(theme_homepage, "_matches_homepage", lambda pid: False)
    assert theme_homepage.is_running() is False
    assert not pidfile.exists()


def test_stop_does_not_kill_unverified_process(tmp_path, monkeypatch):
    pidfile = tmp_path / "homepage.pid"
    pidfile.write_text("12345")
    monkeypatch.setattr(theme_homepage, "PIDFILE", pidfile)
    monkeypatch.setattr(theme_homepage, "_matches_homepage", lambda pid: False)
    called = []
    monkeypatch.setattr(theme_homepage.os, "kill", lambda *args: called.append(args))
    message = theme_homepage.stop()
    assert "no process was terminated" in message
    assert called == []


def test_start_requires_eww_and_python(monkeypatch):
    monkeypatch.setattr(theme_homepage, "is_running", lambda: False)
    monkeypatch.setattr(theme_homepage, "dependency_report", lambda: {
        "eww": False, "python3": True, "hyprctl": False, "playerctl": False,
    })
    assert "missing required dependencies: eww" == theme_homepage.start()
