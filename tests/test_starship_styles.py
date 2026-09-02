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
    "accent": "#ff1493",
    "accent2": "#00e5ff",
    "urgent": "#ff4444",
    "ansi_yellow": "#ffd166",
    "ansi_green": "#66ff99",
}


def render(style):
    return starship.render(COLORS, starship.apply_style(starship.DEFAULT, style))


def test_every_style_is_valid_toml():
    for style in starship.STYLE_NAMES:
        text = render(style)
        parsed = tomllib.loads(text)
        assert parsed["palette"] == "theme"
        assert f"STARSHIP_STYLE = {style}" in text


def test_workspace_has_richer_git_information():
    text = render("workspace")
    parsed = tomllib.loads(text)
    assert "$git_commit" in parsed["format"]
    assert "$git_metrics" in parsed["format"]
    assert ":$remote_branch" in text
    assert "[git_commit]" in text
    assert "[git_metrics]" in text
    assert "${custom.path_end}" in text


def test_hud_uses_dynamic_fill():
    parsed = tomllib.loads(render("hud"))
    assert "$fill" in parsed["format"]
    assert parsed["right_format"] == ""
    assert parsed["fill"]["symbol"] == "·"


def test_operator_has_contextual_custom_modules():
    parsed = tomllib.loads(render("operator"))
    assert "git_age" in parsed["custom"]
    assert "project_status" in parsed["custom"]
    assert ".starship-status" in parsed["custom"]["project_status"]["command"]


def test_minimal_is_quiet():
    parsed = tomllib.loads(render("minimal"))
    assert "$git_commit" not in parsed["format"]
    assert parsed["battery"]["disabled"] is True
    assert parsed["time"]["disabled"] is True
    assert parsed["jobs"]["disabled"] is True


def test_manual_toggle_survives_render():
    values = starship.apply_style(starship.DEFAULT, "workspace")
    values["battery_enabled"] = False
    parsed = tomllib.loads(starship.render(COLORS, values))
    assert parsed["battery"]["disabled"] is True


def test_old_style_names_migrate():
    assert starship.normalize_style("Rounded powerline") == "workspace"
    assert starship.normalize_style("Minimal status") == "minimal"
