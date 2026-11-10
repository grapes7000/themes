import importlib.machinery
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

import theme_effects
import theme_qt_theme_engine
import theme_runtime
import theme_ui
from theme_qt_bridge import ThemeStudioBridge


def test_manual_preview_updates_contracts_and_cancel_restores_saved_theme(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    cfg = tmp_path / "config"
    themes = cfg / "hypr/themes"
    profiles = cfg / "theme-engine/ui-styles/bundled"
    themes.mkdir(parents=True)
    profiles.mkdir(parents=True)
    shutil.copy(ROOT / "themes/catppuccin_frappe.json", themes)
    for profile in (ROOT / "ui-styles").glob("*.json"):
        shutil.copy(profile, profiles)
    active = cfg / "hypr/generated/.active"
    active.parent.mkdir(parents=True)
    active.write_text("catppuccin_frappe\n")
    monkeypatch.setattr(theme_runtime, "CFG", cfg)
    monkeypatch.setattr(theme_runtime, "THEME_DIR", themes)
    monkeypatch.setattr(theme_runtime, "ACTIVE_FILE", active)
    monkeypatch.setattr(theme_effects, "PROFILE_PATH", cfg / "theme-effects.json")
    monkeypatch.setattr(theme_ui, "PROFILE_DIR", profiles.parent)
    monkeypatch.setattr(theme_ui, "STATE_FILE", cfg / "theme-engine/ui-style")
    monkeypatch.setattr(
        theme_ui, "CONTRACT_FILE", cfg / "theme-engine/generated/ui-style.json"
    )
    monkeypatch.setattr(
        theme_qt_theme_engine,
        "DEFAULT_CONTRACT",
        cfg / "theme-engine/generated/theme.json",
    )
    monkeypatch.setattr(
        theme_qt_theme_engine, "DEFAULT_UI_STYLE_CONTRACT", theme_ui.CONTRACT_FILE
    )
    monkeypatch.setattr(
        ThemeStudioBridge, "_read_effects_profile", staticmethod(lambda: None)
    )
    monkeypatch.setattr(
        ThemeStudioBridge, "_clear_effect_override", lambda self, axis: None
    )
    monkeypatch.setattr(theme_runtime, "_run_legacy", lambda name: (True, ""))
    monkeypatch.setattr(
        theme_runtime, "_sync_semantic_wallpaper", lambda name: (False, "")
    )
    monkeypatch.setattr(theme_runtime, "apply_all", lambda theme, components: {})
    monkeypatch.setattr(theme_runtime, "_sync_noctalia", lambda name: (False, ""))
    monkeypatch.setattr(theme_runtime, "_reload_hyprland", lambda: (True, ""))
    monkeypatch.setattr(
        theme_runtime, "_apply_static_wallpaper", lambda name: (False, "")
    )
    monkeypatch.setattr(
        theme_runtime, "_sync_starship_runtime", lambda theme: (False, "")
    )
    app = QGuiApplication.instance() or QGuiApplication([])
    bridge = ThemeStudioBridge("catppuccin_frappe")
    bridge.setLivePreview(False)
    theme_ui.publish(theme_runtime.load_theme("catppuccin_frappe"), "catppuccin_frappe")
    watcher = theme_qt_theme_engine.ThemeBridge()
    engine = QQmlEngine()
    engine.rootContext().setContextProperty("studioBridge", bridge)
    for page, slider_name in (
        ("WindowsPage.qml", "components.windows.gaps_out"),
        ("QuickshellPage.qml", "shell-simple.radius_control"),
        ("StylePage.qml", "style.corner_radius"),
    ):
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(ROOT / "qt-theme-studio/qml/pages" / page))
        )
        instance = component.create()
        assert instance is not None, [error.toString() for error in component.errors()]
        if slider_name:
            window = QQuickWindow()
            window.resize(1000, 1200)
            instance.setParentItem(window.contentItem())
            instance.setWidth(1000)
            instance.setHeight(1200)
            window.show()
            QTest.qWait(100)
            items = [instance]
            slider = None
            while items:
                item = items.pop()
                if item.objectName() == slider_name:
                    slider = item
                    break
                items.extend(item.childItems())
            assert slider is not None
            original = slider.property("value")
            handle = slider.property("handle")
            start = slider.mapToScene(
                QPointF(
                    handle.x() + handle.width() / 2, handle.y() + handle.height() / 2
                )
            ).toPoint()
            end = start + QPointF(70, 0).toPoint()
            QTest.mousePress(window, Qt.MouseButton.LeftButton, pos=start)
            assert slider.property("pressed")
            QTest.mouseMove(window, end, delay=20)
            bridge.stateChanged.emit()
            assert slider.property("pressed")
            changed = slider.property("value")
            assert changed > original, (page, start, end, slider.width())
            handle_center = slider.mapToScene(
                QPointF(
                    handle.x() + handle.width() / 2, handle.y() + handle.height() / 2
                )
            )
            assert abs(handle_center.x() - end.x()) <= 8
            QTest.mouseRelease(window, Qt.MouseButton.LeftButton, pos=end)
            if page == "WindowsPage.qml":
                assert (
                    bridge._editor.draft["components"]["windows"]["gaps_out"] == changed
                )
            elif page == "QuickshellPage.qml":
                assert (
                    bridge._editor.draft["ui_style_overrides"]["metrics"]["radius_control"]
                    == changed
                )
                example = instance.findChild(QObject, "shell-example")
                assert example is not None
                assert example.property("buttonRadius") == changed
                bridge.setRole("accent", "#D04080")
                bridge.setQuickshellValue("components.homepage.bar_opacity", "0.42")
                assert example.property("accentColor").name().upper() == "#D04080"
                assert example.property("barOpacity") == 0.42
            else:
                assert (
                    bridge._editor.draft["components"]["windows"]["corner_radius"]
                    == changed
                )
            window.close()
    bridge.setQuickshellValue("components.homepage.bar_opacity", "0.42")
    bridge.setUiStyleValue("metrics", "radius_surface", "19")
    bridge.setUiStyleValue("metrics", "motion_normal_ms", "320")
    bridge.setWindowValue("components.windows.gaps_in", "13")
    bridge.setWindowValue("components.windows.corner_radius", "21")
    bridge.setWindowValue("components.windows.glow", "12")
    bridge.setWindowValue("style.animation_preset", "custom")
    bridge.setWindowValue("style.custom_bezier_y1", "1.5")
    bridge.setWindowValue("style.workspace_style", "slidevert")
    bridge.setWindowValue("style.layer_animation_enabled", "false")
    bridge.previewNow()
    contract = json.loads((cfg / "theme-engine/generated/theme.json").read_text())
    assert contract["schema_version"] == 1
    style = json.loads(theme_ui.CONTRACT_FILE.read_text())
    QTest.qWait(150)
    assert contract["components"]["homepage"]["bar_opacity"] == 0.42
    assert style["metrics"]["radius_surface"] == 19
    assert style["metrics"]["motion_normal_ms"] == 320
    assert json.loads(watcher.uiMetricsJson)["radius_surface"] == 19
    lua = (cfg / "hypr/generated/theme.lua").read_text()
    assert "gaps_in = 13," in lua
    assert "rounding = 21," in lua
    assert "range = 12," in lua
    assert 'hl.curve("studioCustom", { type = "bezier", points = { { 0.16, 1.5 }' in lua
    assert 'style = "slidevert"' in lua
    assert 'leaf = "layersIn", enabled = false' in lua
    bridge.setWindowValue("style.animation_preset", "spring")
    bridge.setWindowValue("style.spring_dampening", "12")
    bridge.setWindowValue("style.motion_blur_mode", "enabled")
    bridge.setWindowValue("style.wobble_mode", "enabled")
    bridge.previewNow()
    spring_lua = (cfg / "hypr/generated/theme.lua").read_text()
    assert (
        'type = "spring", mass = 1.0, stiffness = 245.0, dampening = 12.0' in spring_lua
    )
    assert (
        'leaf = "windowsMove", enabled = true, speed = 5, spring = "studioCustom"'
        in spring_lua
    )
    assert "motion_blur = { enabled = true, samples = 4 }" in spring_lua
    assert "wobble = { enabled = true, intensity = 0.035" in spring_lua
    if shutil.which("Hyprland"):
        check = subprocess.run(
            [
                "Hyprland",
                "--verify-config",
                "--config",
                str(cfg / "hypr/generated/theme.lua"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert check.returncode == 0, check.stdout + check.stderr
    bridge.setMotionProfile("balanced")
    bridge.setWindowValue("components.windows.blur.size", "11")
    bridge.previewNow()
    profiled = json.loads((cfg / "theme-engine/generated/theme.json").read_text())
    assert profiled["components"]["windows"]["blur"]["size"] == 11
    assert profiled["style"]["spring_dampening"] == 25.0
    assert active.read_text().strip() == "catppuccin_frappe"
    bridge.cancelChanges()
    restored = json.loads((cfg / "theme-engine/generated/theme.json").read_text())
    restored_style = json.loads(theme_ui.CONTRACT_FILE.read_text())
    assert restored["name"] == "catppuccin_frappe"
    assert restored_style["metrics"]["radius_surface"] != 19
    theme_ui.set_override("legacy")
    second = ThemeStudioBridge("catppuccin_frappe")
    second.setLivePreview(False)
    second.followThemeUiStyle()
    assert theme_ui.override_name() is None
    assert second.dirty
    second.cancelChanges()
    assert theme_ui.override_name() == "legacy"
    second.followThemeUiStyle()
    second.saveAndApply()
    second.closeSession()
    assert theme_ui.override_name() is None
    assert app is not None


def test_motion_profile_command_updates_active_theme(tmp_path, monkeypatch):
    cfg = tmp_path / "config"
    themes = cfg / "hypr/themes"
    themes.mkdir(parents=True)
    shutil.copy(ROOT / "themes/catppuccin_frappe.json", themes)
    active = cfg / "hypr/generated/.active"
    active.parent.mkdir(parents=True)
    active.write_text("catppuccin_frappe\n")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(theme_runtime, "CFG", cfg)
    monkeypatch.setattr(theme_runtime, "THEME_DIR", themes)
    monkeypatch.setattr(theme_runtime, "ACTIVE_FILE", active)
    monkeypatch.setattr(theme_effects, "PROFILE_PATH", cfg / "theme-effects.json")
    monkeypatch.setattr(theme_runtime, "apply_saved_theme", lambda name: {})
    loader = importlib.machinery.SourceFileLoader(
        "theme_studio_command", str(ROOT / "bin/theme-studio")
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    monkeypatch.setattr(module, "_sync_starship_runtime_only", lambda: None)
    monkeypatch.setattr(sys, "argv", ["theme", "motion-profile", "balanced"])
    assert module.main() == 0
    saved = json.loads((themes / "catppuccin_frappe.json").read_text())
    assert saved["components"]["windows"]["blur"]["size"] == 5
    assert saved["style"]["spring_dampening"] == 25.0
