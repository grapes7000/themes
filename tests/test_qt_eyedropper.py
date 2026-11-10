import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QColor, QGuiApplication, QImage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

import theme_qt_bridge


def test_wayland_eyedropper_samples_captured_pixels(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(theme_qt_bridge.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(theme_qt_bridge.theme_runtime, "active_theme", lambda: None)
    monkeypatch.setattr(theme_qt_bridge.theme_ui, "override_name", lambda: None)
    monkeypatch.setattr(theme_qt_bridge.ThemeStudioBridge, "_read_effects_profile", staticmethod(lambda: None))
    monkeypatch.setattr(theme_qt_bridge.ThemeStudioBridge, "_load_initial", lambda self, name: None)
    monkeypatch.setattr(theme_qt_bridge.ThemeStudioBridge, "refreshWallpapers", lambda self: None)
    app = QGuiApplication.instance() or QGuiApplication([])
    monkeypatch.setattr(QGuiApplication, "platformName", lambda: "wayland")
    image = QImage(2, 2, QImage.Format.Format_RGB32)
    image.fill(QColor("#123456"))
    data = QByteArray()
    buffer = QBuffer(data)
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    buffer.close()
    monkeypatch.setattr(
        theme_qt_bridge.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, bytes(data), b""),
    )
    bridge = theme_qt_bridge.ThemeStudioBridge()
    assert bridge.captureScreenForEyedropper()
    assert bridge.screenColorAt(10, 10, 100, 100) == "#123456"
    assert app is not None
