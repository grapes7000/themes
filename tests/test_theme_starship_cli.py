from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_theme_starship_use_powerline_renders_powerline_directly(tmp_path):
    home = tmp_path / "home"
    cfg = home / ".config"
    theme_dir = cfg / "hypr" / "themes"
    generated = cfg / "hypr" / "generated"
    studio = tmp_path / "studio"
    theme_dir.mkdir(parents=True)
    generated.mkdir(parents=True)

    subprocess.run(
        ["bash", str(ROOT / "tools" / "unpack-theme-studio.sh"), str(studio)],
        check=True,
        text=True,
        capture_output=True,
    )

    source_theme = json.loads((ROOT / "themes" / "gruvbox-dark.json").read_text(encoding="utf-8"))
    (theme_dir / "gruvbox-dark.json").write_text(json.dumps(source_theme), encoding="utf-8")
    (generated / ".active").write_text("gruvbox-dark\n", encoding="utf-8")

    env = os.environ.copy()
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(cfg)
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "bin"), str(studio)])
    env["THEME_LEGACY_COMMAND"] = "/bin/false"

    proc = subprocess.run(
        [sys.executable, str(ROOT / "bin" / "theme-studio"), "starship", "use", "powerline"],
        env=env,
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr

    output = cfg / "starship.toml"
    text = output.read_text(encoding="utf-8")
    parsed = tomllib.loads(text)
    assert "STARSHIP_STYLE = powerline" in text
    assert parsed["format"].startswith("[](orange)$os$username[](bg:warn fg:orange)$directory")
    assert parsed["username"]["show_always"] is True
    assert "󰉋" not in parsed["directory"]["format"]
    assert "$virtualenv" in parsed["python"]["format"]
    assert "starship style -> powerline" in proc.stdout
