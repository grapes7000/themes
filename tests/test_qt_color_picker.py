import shutil
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

import theme_runtime
import theme_ui
from theme_qt_bridge import ThemeStudioBridge


@pytest.mark.parametrize(
    ("page", "button_text", "role"),
    [("QuickshellPage.qml", "Choose color", "surface_0"), ("PalettePage.qml", "Pick", "bg")],
)
def test_color_picker_opens_and_updates_theme(page, button_text, role, tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    cfg = tmp_path / "config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    themes = cfg / "hypr/themes"
    profiles = cfg / "theme-engine/ui-styles/bundled"
    themes.mkdir(parents=True)
    profiles.mkdir(parents=True)
    shutil.copy(ROOT / "themes/catppuccin_frappe.json", themes)
    for profile in (ROOT / "ui-styles").glob("*.json"):
        shutil.copy(profile, profiles)
    monkeypatch.setattr(theme_runtime, "CFG", cfg)
    monkeypatch.setattr(theme_runtime, "THEME_DIR", themes)
    monkeypatch.setattr(theme_runtime, "ACTIVE_FILE", cfg / "hypr/generated/.active")
    monkeypatch.setattr(theme_ui, "PROFILE_DIR", profiles.parent)
    monkeypatch.setattr(theme_ui, "STATE_FILE", cfg / "theme-engine/ui-style")
    monkeypatch.setattr(ThemeStudioBridge, "_read_effects_profile", staticmethod(lambda: None))
    app = QGuiApplication.instance() or QGuiApplication([])
    bridge = ThemeStudioBridge("catppuccin_frappe")
    bridge.setLivePreview(False)
    engine = QQmlEngine()
    engine.rootContext().setContextProperty("studioBridge", bridge)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(ROOT / "qt-theme-studio/qml/pages" / page)))
    instance = component.create()
    assert instance is not None, [error.toString() for error in component.errors()]
    window = QQuickWindow()
    window.resize(1100, 2400)
    instance.setParentItem(window.contentItem())
    instance.setWidth(1100)
    instance.setHeight(2400)
    window.show()
    QTest.qWait(100)
    if page == "QuickshellPage.qml":
        drawer = instance.findChild(QObject, "shell-preview-drawer")
        inspection = instance.findChild(QObject, "shell-color-inspection")
        assert drawer is not None and inspection is not None
        position = drawer.mapToScene(QPointF(drawer.width() - 10, drawer.height() - 10)).toPoint()
        QTest.mouseClick(window, Qt.MouseButton.RightButton, pos=position)
        assert "Drawer surface and outline" in inspection.property("text")
    if page == "PalettePage.qml":
        directory = instance.findChild(QObject, "palette-prompt-directory")
        inspection = instance.findChild(QObject, "palette-inspection")
        assert directory is not None and inspection is not None
        position = directory.mapToScene(QPointF(directory.width() / 2, directory.height() / 2)).toPoint()
        QTest.mouseClick(window, Qt.MouseButton.RightButton, pos=position)
        assert "Accent (accent)" in inspection.property("text")
        bridge.setRole("accent", "#126ABC")
        QTest.qWait(50)
        assert directory.property("color").name().upper() == "#126ABC"
        assert "#126ABC" in inspection.property("text")
        app_button = instance.findChild(QObject, "palette-app-button")
        logo = instance.findChild(QObject, "palette-fastfetch-logo")
        assert app_button is not None and logo is not None
        assert app_button.property("color").name().upper() == "#126ABC"
        position = app_button.mapToScene(QPointF(app_button.width() / 2, app_button.height() / 2)).toPoint()
        QTest.mouseClick(window, Qt.MouseButton.RightButton, pos=position)
        assert "Text on accent (on_accent)" in inspection.property("text")
        bridge.setRole("ansi_cyan", "#ABC123")
        QTest.qWait(50)
        assert logo.property("color").name().upper() == "#ABC123"
        position = logo.mapToScene(QPointF(logo.width() / 2, logo.height() / 2)).toPoint()
        QTest.mouseClick(window, Qt.MouseButton.RightButton, pos=position)
        assert "Terminal cyan (ansi_cyan)" in inspection.property("text")
    pending = [instance]
    button = None
    while pending:
        item = pending.pop(0)
        if item.property("text") == button_text:
            button = item
            break
        pending.extend(item.childItems())
    assert button is not None
    dialog = next(item for item in instance.findChildren(QObject) if "ColorDialog" in item.metaObject().className())
    position = button.mapToScene(QPointF(button.width() / 2, button.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=position)
    QTest.qWait(50)
    assert dialog.property("visible"), f"{page} color picker did not open"
    dialog.setProperty("selectedColor", QColor("#B34080"))
    dialog.accepted.emit()
    assert bridge._editor.draft["roles"][role].upper() == "#B34080"
    if page == "PalettePage.qml":
        def visible_labels():
            pending = [instance]
            labels = []
            while pending:
                item = pending.pop()
                if item.isVisible():
                    labels.append(item.property("text"))
                pending.extend(item.childItems())
            return labels

        bridge.setRole("text", "#b34080")
        QTest.qWait(50)
        assert "↔ Same color as: Main text" in visible_labels()
        bridge.setRole("text", "#123ABC")
        QTest.qWait(50)
        assert "↔ Same color as: Main text" not in visible_labels()
    window.close()
    assert app is not None
