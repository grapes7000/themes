from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

# theme_runtime's component modules are optional in this focused unit test;
# provide tiny import stubs so the symlink helpers can be tested in isolation.
components = types.ModuleType("theme_components")
components.apply_all = lambda *_args, **_kwargs: {}
sys.modules.setdefault("theme_components", components)

schema = types.ModuleType("theme_schema")
schema.dump_json = lambda _data: "{}"
schema.ensure_theme_schema = lambda data: data
schema.safe_theme_name = lambda name: name
sys.modules.setdefault("theme_schema", schema)

waybar = types.ModuleType("theme_waybar")
waybar.apply = lambda *_args, **_kwargs: {}
sys.modules.setdefault("theme_waybar", waybar)

import theme_runtime


def configure(monkeypatch, tmp_path):
    cfg = tmp_path / "config"
    cache = tmp_path / "cache"
    monkeypatch.setattr(theme_runtime, "CFG", cfg)
    monkeypatch.setattr(theme_runtime, "CACHE", cache)
    monkeypatch.setattr(theme_runtime, "RENDER_ROOT", cache / "theme-engine" / "wallpapers")
    return cfg, cache


def test_publish_current_wallpaper_creates_stable_symlink_chain(monkeypatch, tmp_path):
    cfg, cache = configure(monkeypatch, tmp_path)
    rendered = cache / "theme-engine" / "wallpapers" / "arch-retro" / "nord.png"
    rendered.parent.mkdir(parents=True)
    rendered.write_bytes(b"nord")

    current, homepage = theme_runtime._publish_current_wallpaper(rendered)

    assert current == cache / "theme-engine" / "wallpapers" / "current.png"
    assert homepage == cfg / "quickshell" / "homepage-images" / "theme-wallpaper.png"
    assert current.is_symlink()
    assert homepage.is_symlink()
    assert current.resolve() == rendered.resolve()
    assert homepage.resolve() == rendered.resolve()


def test_publish_current_wallpaper_retargets_links_on_theme_change(monkeypatch, tmp_path):
    _, cache = configure(monkeypatch, tmp_path)
    nord = cache / "theme-engine" / "wallpapers" / "arch-retro" / "nord.png"
    gruvbox = cache / "theme-engine" / "wallpapers" / "arch-retro" / "gruvbox.png"
    nord.parent.mkdir(parents=True)
    nord.write_bytes(b"nord")
    gruvbox.write_bytes(b"gruvbox")

    current, homepage = theme_runtime._publish_current_wallpaper(nord)
    assert homepage.resolve() == nord.resolve()

    theme_runtime._publish_current_wallpaper(gruvbox)
    assert current.resolve() == gruvbox.resolve()
    assert homepage.resolve() == gruvbox.resolve()
