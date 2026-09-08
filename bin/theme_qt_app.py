#!/usr/bin/env python3
"""PySide6/QML entrypoint for Theme Studio."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from theme_qt_bridge import ThemeStudioBridge
from theme_qt_theme_engine import ThemeBridge


def _qml_path() -> Path:
    explicit = os.environ.get("THEME_STUDIO_QML_DIR")
    if explicit:
        return Path(explicit).expanduser() / "Main.qml"

    here = Path(__file__).resolve()
    source_checkout = here.parent.parent / "qt-theme-studio" / "qml" / "Main.qml"
    if source_checkout.exists():
        return source_checkout

    installed = Path.home() / ".local" / "share" / "theme-studio" / "qt" / "qml" / "Main.qml"
    return installed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Qt Theme Studio")
    parser.add_argument("--theme", help="theme to open initially")
    args = parser.parse_args(argv)

    app = QGuiApplication(sys.argv if argv is None else [sys.argv[0], *argv])
    app.setApplicationName("Theme Studio")
    app.setOrganizationName("grapes7000")
    app.setDesktopFileName("theme-studio")

    studio_bridge = ThemeStudioBridge(args.theme)
    theme_bridge = ThemeBridge()

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("studioBridge", studio_bridge)
    engine.rootContext().setContextProperty("themeBridge", theme_bridge)

    qml_path = _qml_path()
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        print(f"theme: failed to load Qt UI: {qml_path}", file=sys.stderr)
        return 2

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
