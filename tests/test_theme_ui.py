import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

import theme_ui


def _profile(name: str) -> dict:
    return {
        "schema_version": 1,
        "name": name,
        "description": name,
        "metrics": {"control_height": 30},
        "patterns": {"surface": "flat"},
        "rules": {},
    }


def _configure(tmp_path, monkeypatch):
    profiles = tmp_path / "ui-styles"
    profiles.mkdir()
    for name in ("precision", "legacy", "win95"):
        (profiles / f"{name}.json").write_text(json.dumps(_profile(name)))
    monkeypatch.setattr(theme_ui, "PROFILE_DIR", profiles)
    monkeypatch.setattr(theme_ui, "STATE_FILE", tmp_path / "ui-style")
    monkeypatch.setattr(theme_ui, "CONTRACT_FILE", tmp_path / "generated" / "ui-style.json")


def test_default_is_precision(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch)
    assert theme_ui.resolved_name({"name": "plain"}) == ("precision", "default")


def test_theme_link_is_used_in_auto_mode(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch)
    theme_ui.set_override(None)
    assert theme_ui.resolved_name({"name": "retro", "ui_style": "win95"}) == ("win95", "theme")


def test_explicit_override_wins_over_theme_link(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch)
    theme_ui.set_override("legacy")
    assert theme_ui.resolved_name({"name": "retro", "ui_style": "win95"}) == ("legacy", "override")


def test_publish_writes_resolved_contract(tmp_path, monkeypatch):
    _configure(tmp_path, monkeypatch)
    theme_ui.set_override("win95")
    contract = theme_ui.publish({"name": "graphite", "ui_style": "precision"}, "graphite")
    written = json.loads(theme_ui.CONTRACT_FILE.read_text())
    assert contract["name"] == "win95"
    assert written["resolved_from"] == "override"
    assert written["theme"] == "graphite"
