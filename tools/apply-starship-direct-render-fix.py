from pathlib import Path

path = Path('bin/theme-studio')
text = path.read_text(encoding='utf-8')

old_import = '''    normalize_style as normalize_starship_style,
    profile as starship_profile,
    save as save_starship_profile,
)'''
new_import = '''    normalize_style as normalize_starship_style,
    profile as starship_profile,
    render as render_starship,
    save as save_starship_profile,
)'''
if old_import not in text:
    raise SystemExit('expected Starship import block not found')
text = text.replace(old_import, new_import, 1)

old = '''    code = run_legacy(["starship"])
    if code != 0:
        return code
    _sync_starship_runtime_only()
    print(f"starship style -> {current}")
    return 0
'''
new = '''    theme_name = theme_runtime.active_theme()
    if not theme_name:
        print("theme starship: no active theme", file=sys.stderr)
        return 2
    try:
        theme = theme_runtime.load_theme(theme_name)
        roles = dict(theme.get("roles", {}))
        if not roles:
            raise ValueError(f"theme '{theme_name}' has no roles")
        cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser()
        output = cfg / "starship.toml"
        output.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_starship(roles, values)
        fd, temporary = tempfile.mkstemp(prefix=".starship.", suffix=".tmp", dir=output.parent, text=True)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(rendered)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, output)
        finally:
            temporary_path.unlink(missing_ok=True)
    except Exception as exc:
        print(f"theme starship: {exc}", file=sys.stderr)
        return 1

    _sync_starship_runtime_only()
    print(f"starship -> {theme_name}")
    print(f"starship style -> {current}")
    return 0
'''
if old not in text:
    raise SystemExit('expected legacy Starship handoff not found')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')

test = Path('tests/test_theme_starship_cli.py')
test.write_text('''from __future__ import annotations

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
    (generated / ".active").write_text("gruvbox-dark\\n", encoding="utf-8")

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
''', encoding='utf-8')
