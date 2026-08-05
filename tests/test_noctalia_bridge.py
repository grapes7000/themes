from pathlib import Path
import importlib.util
from importlib.machinery import SourceFileLoader


def load_module(path: Path):
    loader = SourceFileLoader("theme_noctalia", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_palette_maps_semantic_roles():
    module = load_module(Path(__file__).parents[1] / "bin" / "theme-noctalia")
    theme = {
        "dark": True,
        "roles": {
            "bg": "#101010", "bg_alt": "#202020", "text": "#f0f0f0",
            "text_dim": "#aaaaaa", "accent": "#ff0091", "accent2": "#00ccff",
            "urgent": "#ff3344", "ansi_black": "#000000", "ansi_white": "#ffffff",
        },
    }
    variant = module.make_variant(theme)
    assert variant["mSurface"] == "#101010"
    assert variant["mPrimary"] == "#ff0091"
    assert variant["mSecondary"] == "#00ccff"
    assert variant["terminal"]["background"] == "#101010"


def test_set_key_creates_and_updates_section():
    module = load_module(Path(__file__).parents[1] / "bin" / "theme-noctalia")
    lines = module.set_key([], "theme", "source", '"custom"')
    lines = module.set_key(lines, "theme", "source", '"builtin"')
    assert "".join(lines).count("source =") == 1
    assert 'source = "builtin"' in "".join(lines)


def test_overlap_filter_preserves_unrelated_templates():
    module = load_module(Path(__file__).parents[1] / "bin" / "theme-noctalia")
    builtins, community = module.overlap_templates({"kitty", "vscode"})
    assert builtins == {"kitty"}
    assert community == {"vscode"}
    assert "btop" not in builtins
