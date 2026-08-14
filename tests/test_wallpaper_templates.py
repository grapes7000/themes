from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("wallgen_semantic", str(ROOT / "bin" / "wallgen"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
wallgen = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
LOADER.exec_module(wallgen)


def configure(monkeypatch, tmp_path):
    cfg = tmp_path / "config"
    cache = tmp_path / "cache"
    monkeypatch.setattr(wallgen, "CFG", cfg)
    monkeypatch.setattr(wallgen, "CACHE", cache)
    monkeypatch.setattr(wallgen, "THEME_DIR", cfg / "hypr" / "themes")
    monkeypatch.setattr(wallgen, "WALL_DIR", cfg / "hypr" / "wallpapers")
    monkeypatch.setattr(wallgen, "TEMPLATE_ROOT", cfg / "theme-engine" / "wallpaper-templates")
    monkeypatch.setattr(wallgen, "ACTIVE_TEMPLATE_FILE", cfg / "theme-engine" / "wallpaper-template")
    monkeypatch.setattr(wallgen, "RENDER_ROOT", cache / "theme-engine" / "wallpapers")
    return cfg, cache


def write_template(cfg: Path, image: Image.Image, name="sample"):
    root = cfg / "theme-engine" / "wallpaper-templates" / name
    root.mkdir(parents=True)
    image.save(root / "source.png")
    (root / "template.json").write_text(json.dumps({
        "version": 1,
        "name": name,
        "source": "source.png",
        "regions": [
            {"source": "#282828", "role": "bg"},
            {"source": "#cc241d", "role": "ansi_red"},
        ],
        "render": {"max_blend_error": 14.0},
    }), encoding="utf-8")


def test_arch_palette_suggestions():
    expected = {
        "#282828": "bg",
        "#ebdbb2": "text",
        "#689d6a": "ansi_green",
        "#458588": "ansi_blue",
        "#d79921": "ansi_yellow",
        "#cc241d": "ansi_red",
    }
    assert {color: wallgen.suggest_role(color) for color in expected} == expected


def test_discovery_ignores_tiny_fringe(tmp_path):
    image = Image.new("RGB", (100, 10), "#282828")
    for x in range(20, 40):
        for y in range(10):
            image.putpixel((x, y), (104, 157, 106))
    for x in range(40, 60):
        for y in range(10):
            image.putpixel((x, y), (69, 133, 136))
    image.putpixel((0, 0), (41, 42, 41))
    path = tmp_path / "flat.png"
    image.save(path)
    colors = [entry["color"] for entry in wallgen.discover_regions(path)]
    assert colors[:3] == ["#282828", "#689d6a", "#458588"]
    assert "#292a29" not in colors


def test_render_recolors_flat_anchors_and_edge_blend(monkeypatch, tmp_path):
    cfg, cache = configure(monkeypatch, tmp_path)
    source = Image.new("RGBA", (3, 1))
    source.putdata([(40, 40, 40, 255), (122, 38, 34, 255), (204, 36, 29, 255)])
    write_template(cfg, source)
    roles = {"bg": "#2e3440", "ansi_red": "#bf616a", "accent": "#88c0d0", "text": "#eceff4"}
    out = wallgen.render_template("sample", "nord", roles)
    assert out == cache / "theme-engine" / "wallpapers" / "sample" / "nord.png"
    pixels = list(Image.open(out).convert("RGB").getdata())
    assert pixels[0] == (46, 52, 64)
    assert pixels[2] == (191, 97, 106)
    assert pixels[1] not in ((122, 38, 34), pixels[0], pixels[2])


def test_role_fallbacks():
    roles = {"bg": "#000000", "text": "#ffffff", "accent": "#ff00ff", "accent2": "#00ffff", "urgent": "#ff0000"}
    assert wallgen.resolve_role(roles, "ansi_red") == "#ff0000"
    assert wallgen.resolve_role(roles, "ansi_green") == "#00ffff"
    assert wallgen.resolve_role(roles, "ansi_blue") == "#00ffff"


def test_import_and_activate(monkeypatch, tmp_path):
    cfg, _ = configure(monkeypatch, tmp_path)
    source = tmp_path / "input.png"
    image = Image.new("RGB", (20, 10), "#282828")
    for x in range(10, 20):
        for y in range(10):
            image.putpixel((x, y), (204, 36, 29))
    image.save(source)
    payload = wallgen.import_template(source, "My Template", min_percent=1.0, accept_suggestions=True)
    assert payload["name"] == "my-template"
    assert wallgen.active_template() == "my-template"
    root = cfg / "theme-engine" / "wallpaper-templates" / "my-template"
    assert (root / "source.png").exists()
    assert json.loads((root / "template.json").read_text())["regions"] == [
        {"source": "#282828", "role": "bg"},
        {"source": "#cc241d", "role": "ansi_red"},
    ]


def test_builtin_materializes_from_installed_wallpaper(monkeypatch, tmp_path):
    cfg, _ = configure(monkeypatch, tmp_path)
    wallgen.WALL_DIR.mkdir(parents=True)
    source = Image.new("RGB", (2, 1), "#282828")
    source.putpixel((1, 0), (235, 219, 178))
    source.save(wallgen.WALL_DIR / "arch-retro-source.png")
    wallgen.set_active_template("arch-retro")
    assert wallgen.active_template() == "arch-retro"
    template = json.loads((wallgen.TEMPLATE_ROOT / "arch-retro" / "template.json").read_text())
    assert template["builtin"] is True
    assert any(region == {"source": "#458588", "role": "ansi_blue"} for region in template["regions"])


def test_none_keeps_classic_wallpaper(monkeypatch, tmp_path):
    cfg, _ = configure(monkeypatch, tmp_path)
    image = Image.new("RGBA", (2, 1), "#282828")
    image.putpixel((1, 0), (204, 36, 29, 255))
    write_template(cfg, image)
    normal = wallgen.WALL_DIR / "nord.png"
    normal.parent.mkdir(parents=True)
    normal.write_bytes(b"keep")
    wallgen.set_active_template("sample")
    wallgen.set_active_template(None)
    assert normal.read_bytes() == b"keep"
