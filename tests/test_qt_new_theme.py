import json
import shutil
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

import theme_runtime
from theme_qt_theme_engine import ThemeBridge
from theme_qt_bridge import ThemeStudioBridge


def test_save_as_preserves_existing_theme_and_rejects_its_name(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    themes = tmp_path / "config/hypr/themes"
    themes.mkdir(parents=True)
    source = themes / "catppuccin_frappe.json"
    shutil.copy(ROOT / "themes/catppuccin_frappe.json", source)
    original = source.read_bytes()
    monkeypatch.setattr(theme_runtime, "THEME_DIR", themes)
    monkeypatch.setattr(theme_runtime, "active_theme", lambda: None)
    monkeypatch.setattr(theme_runtime, "apply_saved_theme", lambda name: None)
    monkeypatch.setattr(ThemeStudioBridge, "_read_effects_profile", staticmethod(lambda: None))
    app = QGuiApplication.instance() or QGuiApplication([])
    bridge = ThemeStudioBridge("catppuccin_frappe")
    bridge.setLivePreview(False)
    bridge.generatePalette("#B34080", True)
    bridge.duplicateTheme("catppuccin_frappe")
    assert source.read_bytes() == original
    assert bridge.dirty
    engine = QQmlEngine()
    engine.rootContext().setContextProperty("studioBridge", bridge)
    theme_bridge = ThemeBridge()
    engine.rootContext().setContextProperty("themeBridge", theme_bridge)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(ROOT / "qt-theme-studio/qml/Main.qml")))
    window = component.create()
    assert window is not None, [error.toString() for error in component.errors()]
    assert isinstance(window.property("contentItem"), QQuickItem)
    QTest.qWait(100)

    def click_button(label):
        pending = [window.property("contentItem")]
        pending.extend(
            item.property("contentItem")
            for item in window.findChildren(QObject)
            if item.property("title") == "How would you like to save?"
        )
        while pending:
            item = pending.pop()
            if item.isVisible() and item.property("text") == label:
                position = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
                QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=position)
                QTest.qWait(50)
                return
            pending.extend(item.childItems())
        pytest.fail(f"Visible button not found: {label}")

    click_button("Save & Apply")
    click_button("Save as a new theme")
    field = next(item for item in window.findChildren(QObject) if item.property("placeholderText") == "New theme name")
    field.setProperty("text", "My New Theme")
    dialog = next(item for item in window.findChildren(QObject) if item.property("title") == "Save as a new theme")
    dialog.accept()
    saved = json.loads((themes / "My_New_Theme.json").read_text())
    assert source.read_bytes() == original
    assert saved["name"] == "My_New_Theme"
    assert bridge.themeName == "My_New_Theme"
    QTest.qWait(50)
    click_button("New theme")
    field = next(item for item in window.findChildren(QObject) if item.property("placeholderText") == "Theme name")
    field.setProperty("text", "Another Theme")
    dialog = next(item for item in window.findChildren(QObject) if item.property("title") == "Create a custom theme")
    assert dialog.property("visible")
    dialog.accept()
    assert (themes / "Another_Theme.json").exists()
    assert bridge.themeName == "Another_Theme"
    window.close()
    assert app is not None
