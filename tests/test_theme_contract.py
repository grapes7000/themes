"""Tests for the stable desktop theme contract."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.sys.path.insert(0, str(ROOT / "bin"))
spec = importlib.util.spec_from_loader(
    "theme_contract_main",
    importlib.machinery.SourceFileLoader("theme_contract_main", str(ROOT / "bin/theme")),
)
theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)


def test_contract_preserves_data_and_resolves_roles(tmp_path):
    destination = tmp_path / "generated/theme.json"
    theme.THEME_CONTRACT_FILE = str(destination)
    original = {
        "name": "old-name",
        "dark": True,
        "custom": {"keep": [1, 2, 3]},
        "roles": {"bg": "#000000"},
        "style": {"gaps": 7},
    }
    roles = {"bg": "#000000", "surface_0": "#000000"}
    style = {"gaps": 7, "corner_radius": 4}

    result = theme.gen_theme_contract("example", original, roles, style)
    loaded = json.loads(destination.read_text())

    assert loaded == result
    assert loaded["name"] == "example"
    assert loaded["custom"] == original["custom"]
    assert loaded["roles"] == roles
    assert loaded["style"] == style


def test_contract_replace_is_atomic_and_leaves_no_temporary_file(tmp_path):
    destination = tmp_path / "generated/theme.json"
    theme.THEME_CONTRACT_FILE = str(destination)
    destination.parent.mkdir(parents=True)
    destination.write_text('{"old": true}\n')

    theme.gen_theme_contract("new", {"dark": False}, {"bg": "#ffffff"}, {})

    assert json.loads(destination.read_text())["name"] == "new"
    assert list(destination.parent.glob(".theme-*.tmp")) == []
