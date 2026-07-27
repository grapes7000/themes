"""Focused tests for the Eww homepage runtime."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))
import theme_homepage

ROLES = {
    "bg": "#1e1e2e", "bg_alt": "#181825", "text": "#cdd6f4",
    "text_dim": "#a6adc8", "accent": "#cba6f7", "accent2": "#89b4fa",
    "border_normal": "#313244",
}
STYLE = {"corner_radius": 14}


def _balanced_yuck(text: str) -> bool:
    """Small static guard for generated delimiters, strings, comments and commands."""
    depth = 0
    in_string = False
    in_command = False
    escaped = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(";") and not in_string and not in_command:
            continue
        for char in line:
            if escaped:
                escaped = False
                continue
            if char == "\\" and in_string:
                escaped = True
                continue
            if char == '"' and not in_command:
                in_string = not in_string
                continue
            if char == "`" and not in_string:
                in_command = not in_command
                continue
            if in_string or in_command:
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth < 0:
                    return False
    return depth == 0 and not in_string and not in_command


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
    assert ".stat-ring" in scss
    assert ".media-control-primary" in scss
    assert ".homepage-tint" in scss


def test_workspace_is_dynamic_and_clickable():
    yuck = theme_homepage.render_yuck({"alignment": "left"})
    assert "workspace-state" in yuck
    assert "'.active'" in yuck
    assert "switch-workspace.py" in yuck
    assert "ws == 1" not in yuck


def test_overlay_is_fullscreen_with_fixed_widget_column(monkeypatch):
    monkeypatch.setattr(theme_homepage, "_monitor_size", lambda: (1920, 1080))
    yuck = theme_homepage.render_yuck({"alignment": "right"})
    assert 'anchor "top right"' in yuck
    assert ':width "1920px"' in yuck
    assert ':height "1080px"' in yuck
    assert ':halign "end"' in yuck
    assert ':width 430' in yuck
    assert ':stacking "bottom"' in yuck
    assert ':exclusive false' in yuck
    assert ':focusable false' in yuck
    assert 'homepage-tint" :hexpand true :vexpand true' in yuck


def test_generated_labels_are_escaped():
    yuck = theme_homepage.render_yuck({"alignment": "left"}, 'bad"\nname', 'calm"')
    assert 'bad\\" name' in yuck
    assert 'calm\\"' in yuck


def test_wallpaper_priority_and_background_widget(tmp_path, monkeypatch):
    monkeypatch.setattr(theme_homepage, "CFG", tmp_path)
    generated = tmp_path / "hypr" / "wallpapers" / "rose-pine.png"
    generated.parent.mkdir(parents=True)
    generated.write_bytes(b"png")
    monkeypatch.setattr(theme_homepage, "_monitor_size", lambda: (2560, 1440))
    yuck = theme_homepage.render_yuck({"alignment": "left"}, "rose-pine")
    assert str(generated) in yuck
    assert 'image-width 2560' in yuck
    assert 'image-height 1440' in yuck
    assert 'homepage-background" :path' in yuck
    assert ':hexpand true :vexpand true' in yuck
    assert 'homepage-background-fallback' not in yuck
    assert 'preserve-aspect-ratio' not in yuck


def test_missing_wallpaper_uses_colored_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(theme_homepage, "CFG", tmp_path)
    yuck = theme_homepage.render_yuck({"alignment": "left"}, "missing")
    assert 'homepage-background-fallback' in yuck


def test_system_stats_are_graphical():
    yuck = theme_homepage.render_yuck({"alignment": "left"})
    assert yuck.count("circular-progress") == 3
    assert ":value {sysinfo.cpu}" in yuck
    assert ":value {sysinfo.mem_percent}" in yuck
    assert ":value {sysinfo.disk}" in yuck
    assert "SYSTEM UPTIME" in yuck


def test_media_hover_layout_art_and_controls():
    yuck = theme_homepage.render_yuck({"alignment": "left"})
    assert "media-hovered" in yuck
    assert '${EWW_CMD} update media-hovered=true' in yuck
    assert ':transition "crossfade"' in yuck
    assert ':image-width 354' in yuck
    assert ':image-width 158' in yuck
    assert "media.title" in yuck and "media.artist" in yuck
    assert "media-control.py'} previous" not in yuck  # f-string must render an absolute script path
    assert "media-control.py previous" in yuck
    assert "media-control.py play-pause" in yuck
    assert "media-control.py next" in yuck
    assert '{media.playing ? "󰏤" : "󰐊"}' in yuck


def test_generated_yuck_has_balanced_delimiters():
    yuck = theme_homepage.render_yuck({"alignment": "left"}, "rose-pine", "polished")
    assert _balanced_yuck(yuck)


def test_helpers_are_python_and_json_safe():
    scripts = theme_homepage.render_scripts()
    assert set(scripts) == {
        "sysinfo.py", "media.py", "media-control.py", "workspaces.py", "switch-workspace.py"
    }
    assert all(value.startswith("#!/usr/bin/env python3") for value in scripts.values())
    assert "json.dumps" in scripts["media.py"]
    assert "re.fullmatch" in scripts["switch-workspace.py"]
    assert "shell=True" not in "".join(scripts.values())


def test_cpu_uses_delta_sample_and_numeric_percentages():
    script = theme_homepage.render_scripts()["sysinfo.py"]
    assert "delta_total" in script
    assert "delta_idle" in script
    assert "theme-homepage-cpu.json" in script
    assert '"mem_percent"' in script
    assert "max(0, min(100" in script


def test_media_helper_supports_cached_album_art():
    script = theme_homepage.render_scripts()["media.py"]
    assert '"mpris:artUrl"' in script
    assert "urlopen" in script
    assert "MAX_ART_BYTES" in script
    assert "theme-homepage" in script
    assert '"playing": status == "Playing"' in script


def test_helpers_run_with_missing_optional_dependencies(tmp_path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    for name, content in theme_homepage.render_scripts().items():
        (scripts_dir / name).write_text(content)

    env = dict(os.environ)
    env["PATH"] = str(tmp_path / "empty-path")
    env["XDG_RUNTIME_DIR"] = str(tmp_path / "runtime")
    env["XDG_CACHE_HOME"] = str(tmp_path / "cache")

    sysinfo = subprocess.run(
        [sys.executable, str(scripts_dir / "sysinfo.py")], env=env,
        check=True, capture_output=True, text=True,
    )
    stats = json.loads(sysinfo.stdout)
    assert 0 <= stats["cpu"] <= 100
    assert 0 <= stats["mem_percent"] <= 100
    assert 0 <= stats["disk"] <= 100

    media = subprocess.run(
        [sys.executable, str(scripts_dir / "media.py")], env=env,
        check=True, capture_output=True, text=True,
    )
    media_data = json.loads(media.stdout)
    assert media_data["visible"] is False
    assert media_data["art"] == ""

    workspaces = subprocess.run(
        [sys.executable, str(scripts_dir / "workspaces.py")], env=env,
        check=True, capture_output=True, text=True,
    )
    assert json.loads(workspaces.stdout)["workspaces"] == [1, 2, 3, 4, 5]

    control = subprocess.run(
        [sys.executable, str(scripts_dir / "media-control.py"), "next"], env=env,
        check=False, capture_output=True, text=True,
    )
    assert control.returncode == 2


def test_missing_pid_is_not_running(tmp_path, monkeypatch):
    monkeypatch.setattr(theme_homepage, "PIDFILE", tmp_path / "missing.pid")
    monkeypatch.setattr(theme_homepage, "_ping_daemon", lambda env=None: False)
    assert theme_homepage.is_running() is False


def test_unrelated_pid_is_never_treated_as_homepage(tmp_path, monkeypatch):
    pidfile = tmp_path / "homepage.pid"
    pidfile.write_text(str(os.getpid()))
    monkeypatch.setattr(theme_homepage, "PIDFILE", pidfile)
    monkeypatch.setattr(theme_homepage, "_matches_homepage", lambda pid: False)
    monkeypatch.setattr(theme_homepage, "_ping_daemon", lambda env=None: False)
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


def test_defpoll_vars_have_json_initial_values():
    yuck = theme_homepage.render_yuck({"alignment": "left"})
    assert ':initial "{\\"cpu\\":0' in yuck
    assert ':initial "{\\"visible\\":false' in yuck
    assert ':initial "{\\"active\\":1' in yuck


def test_clean_stale_socket_removes_orphan(tmp_path, monkeypatch):
    import socket as _socket
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    sock_path = runtime / "eww-server_deadbeef"
    server = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    server.bind(str(sock_path))
    server.close()
    assert sock_path.exists()
    monkeypatch.setattr(theme_homepage, "RUNTIME_DIR", runtime)
    monkeypatch.setattr(theme_homepage, "_ping_daemon", lambda env=None: False)
    theme_homepage._clean_stale_socket()
    assert not sock_path.exists()


def test_clean_stale_socket_preserves_live_daemon(tmp_path, monkeypatch):
    import socket as _socket
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    sock_path = runtime / "eww-server_deadbeef"
    server = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    server.bind(str(sock_path))
    server.close()
    monkeypatch.setattr(theme_homepage, "RUNTIME_DIR", runtime)
    monkeypatch.setattr(theme_homepage, "_ping_daemon", lambda env=None: True)
    theme_homepage._clean_stale_socket()
    assert sock_path.exists()


def test_start_reports_daemon_stderr_when_launch_fails(monkeypatch):
    monkeypatch.setattr(theme_homepage, "is_running", lambda: False)
    monkeypatch.setattr(theme_homepage, "dependency_report",
                        lambda: {"eww": True, "python3": True, "hyprctl": True, "playerctl": True})
    monkeypatch.setattr(theme_homepage.Path, "is_file", lambda self: True)
    monkeypatch.setattr(theme_homepage, "_clean_pidfile", lambda: None)
    monkeypatch.setattr(theme_homepage, "_clean_stale_socket", lambda: None)
    monkeypatch.setattr(theme_homepage, "_ping_daemon", lambda env=None: False)
    monkeypatch.setattr(theme_homepage, "_wait_for_daemon", lambda env, timeout=3.0: False)

    class FakePopen:
        def __init__(self, *args, **kwargs):
            self.pid = 9999
        def poll(self):
            return 1
        def communicate(self, timeout=None):
            return b"", b"daemon boom"

    monkeypatch.setattr(theme_homepage.subprocess, "Popen", FakePopen)
    message = theme_homepage.start()
    assert "daemon boom" in message


def test_start_requires_eww_and_python(monkeypatch):
    monkeypatch.setattr(theme_homepage, "is_running", lambda: False)
    monkeypatch.setattr(theme_homepage, "dependency_report", lambda: {
        "eww": False, "python3": True, "hyprctl": False, "playerctl": False,
    })
    assert "missing required dependencies: eww" == theme_homepage.start()


def test_media_helper_and_controls_with_fake_playerctl(tmp_path):
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    for name, content in theme_homepage.render_scripts().items():
        path = scripts_dir / name
        path.write_text(content)
        path.chmod(0o755)

    art = tmp_path / "cover.png"
    art.write_bytes(b"fake image bytes")
    log = tmp_path / "playerctl.log"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    playerctl = fake_bin / "playerctl"
    playerctl.write_text(f'''#!/bin/sh
case "$1:$2" in
  status:) printf '%s\\n' Playing ;;
  metadata:title) printf '%s\\n' 'Test Song' ;;
  metadata:artist) printf '%s\\n' 'Test Artist' ;;
  metadata:album) printf '%s\\n' 'Test Album' ;;
  metadata:mpris:artUrl) printf '%s\\n' 'file://{art}' ;;
  previous:|play-pause:|next:) printf '%s\\n' "$1" >> '{log}' ;;
esac
''')
    playerctl.chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}:{os.environ.get('PATH', '')}"
    env["XDG_CACHE_HOME"] = str(tmp_path / "cache")

    media = subprocess.run(
        [sys.executable, str(scripts_dir / "media.py")], env=env,
        check=True, capture_output=True, text=True,
    )
    data = json.loads(media.stdout)
    assert data == {
        "visible": True,
        "playing": True,
        "status": "Playing",
        "status_label": "NOW PLAYING",
        "title": "Test Song",
        "artist": "Test Artist",
        "album": "Test Album",
        "art": str(art),
    }

    control = subprocess.run(
        [sys.executable, str(scripts_dir / "media-control.py"), "play-pause"],
        env=env, check=False, capture_output=True, text=True,
    )
    assert control.returncode == 0
    assert log.read_text().strip() == "play-pause"
