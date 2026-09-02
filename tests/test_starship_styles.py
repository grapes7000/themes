from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

import theme_starship as starship  # noqa: E402

COLORS = {
    "bg": "#101010",
    "bg_alt": "#202020",
    "text": "#eeeeee",
    "text_dim": "#888888",
    "accent": "#c58a3a",
    "accent2": "#4e94a8",
    "urgent": "#c94f5f",
    "ansi_yellow": "#e6bb55",
    "ansi_green": "#78ad76",
}

ALT_COLORS = {
    "bg": "#090b0d",
    "bg_alt": "#171a1d",
    "text": "#e6e2d9",
    "text_dim": "#7b7f83",
    "accent": "#934f85",
    "accent2": "#5d8b66",
    "urgent": "#c94f5f",
    "ansi_yellow": "#e6bb55",
    "ansi_green": "#78ad76",
}


def render(style, colors=COLORS):
    return starship.render(colors, starship.apply_style(starship.DEFAULT, style))


def test_every_style_is_valid_toml():
    for style in starship.STYLE_NAMES:
        text = render(style)
        parsed = tomllib.loads(text)
        assert parsed["palette"] == "theme"
        assert f"STARSHIP_STYLE = {style}" in text


def test_workspace_is_the_original_powerline_prompt():
    parsed = tomllib.loads(render("workspace"))
    fmt = parsed["format"]
    assert fmt.startswith("[](fg:surface)$os$username$hostname")
    assert "$directory" in fmt
    assert "${custom.git_connector}$git_branch$git_state$git_status${custom.git_end}" in fmt
    assert "$git_commit" not in fmt
    assert "$git_metrics" not in fmt
    assert parsed["directory"]["style"] == "bold fg:bg bg:accent"
    assert ":$remote_branch" in parsed["git_branch"]["format"]
    assert "${custom.path_end}" in fmt


def test_original_os_and_git_glyph_codepoints_are_restored():
    parsed = tomllib.loads(render("workspace"))
    assert parsed["os"]["symbols"]["Arch"].strip() == ""
    assert parsed["os"]["symbols"]["CachyOS"].strip() == ""
    assert parsed["os"]["symbols"]["Debian"].strip() == ""
    assert parsed["os"]["symbols"]["Fedora"].strip() == ""
    assert parsed["os"]["symbols"]["Ubuntu"].strip() == ""
    assert parsed["os"]["symbols"]["Mint"].strip() == ""
    assert parsed["os"]["symbols"]["Linux"].strip() == ""
    assert parsed["os"]["symbols"]["Macos"].strip() == ""
    assert parsed["os"]["symbols"]["Windows"].strip() == ""
    assert parsed["git_branch"]["symbol"].strip() == ""


def test_layouts_are_structurally_distinct():
    docs = {style: tomllib.loads(render(style)) for style in starship.STYLE_NAMES}
    formats = {style: doc["format"] for style, doc in docs.items()}
    assert len(set(formats.values())) == len(starship.STYLE_NAMES)
    assert "$fill" not in formats["workspace"]
    assert "$fill" in formats["hud"]
    assert "custom.muted_git_connector" in formats["muted"]
    assert "custom.neon_git_connector" in formats["neon"]
    assert "OPERATOR" in formats["operator"]


def test_muted_uses_neutral_workspace_like_segments():
    parsed = tomllib.loads(render("muted"))
    assert parsed["directory"]["style"] == "bold fg:fg bg:bg"
    assert parsed["git_branch"]["style"] == "bold fg:fg bg:surface"
    assert parsed["os"]["style"] == "bold fg:muted bg:surface"
    assert "SYS " not in parsed["format"]


def test_neon_is_derived_from_active_theme_accents():
    first = tomllib.loads(render("neon", COLORS))["palettes"]["theme"]
    second = tomllib.loads(render("neon", ALT_COLORS))["palettes"]["theme"]
    assert first["neon"] != COLORS["accent"]
    assert first["neon2"] != COLORS["accent2"]
    assert second["neon"] != first["neon"]
    assert second["neon2"] != first["neon2"]
    assert first["neon"].startswith("#") and len(first["neon"]) == 7
    assert first["neon2"].startswith("#") and len(first["neon2"]) == 7


def test_neon_uses_neon_palette_for_filled_segments():
    parsed = tomllib.loads(render("neon"))
    assert parsed["directory"]["style"] == "bold fg:bg bg:neon"
    assert parsed["git_branch"]["style"] == "bold fg:bg bg:neon2"
    assert parsed["os"]["style"] == "bold fg:neon bg:surface"
    assert parsed["character"]["success_symbol"].endswith("(bold fg:neon)")


def test_operator_has_valid_contextual_custom_modules():
    parsed = tomllib.loads(render("operator"))
    assert "git_age" in parsed["custom"]
    assert "project_status" in parsed["custom"]
    command = parsed["custom"]["project_status"]["command"]
    condition = parsed["custom"]["project_status"]["when"]
    assert ".starship-status" in command
    assert '"$root/.starship-status"' in command
    assert '"$root/.starship-status"' in condition


def test_minimal_is_quiet():
    parsed = tomllib.loads(render("minimal"))
    assert "$git_commit" not in parsed["format"]
    assert parsed["battery"]["disabled"] is True
    assert parsed["time"]["disabled"] is True
    assert parsed["jobs"]["disabled"] is True


def test_all_layouts_recolor_from_active_theme_roles():
    for style in starship.STYLE_NAMES:
        first = tomllib.loads(render(style, COLORS))["palettes"]["theme"]
        second = tomllib.loads(render(style, ALT_COLORS))["palettes"]["theme"]
        assert first != second
        assert first["accent"] == COLORS["accent"]
        assert second["accent"] == ALT_COLORS["accent"]
        assert second["accent2"] == ALT_COLORS["accent2"]


def test_manual_toggle_survives_render():
    values = starship.apply_style(starship.DEFAULT, "workspace")
    values["battery_enabled"] = False
    parsed = tomllib.loads(starship.render(COLORS, values))
    assert parsed["battery"]["disabled"] is True


def test_bad_feature_branch_git_icon_migrates():
    assert starship._GLYPH_MIGRATIONS[chr(0xF0418)] == ""


def test_old_style_names_migrate():
    assert starship.normalize_style("Rounded powerline") == "workspace"
    assert starship.normalize_style("Minimal status") == "minimal"
    assert starship.normalize_style("Focused development") == "muted"
