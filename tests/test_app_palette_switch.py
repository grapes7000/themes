"""Regression checks for applying a new palette over a previous app theme."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bin'))
spec = importlib.util.spec_from_loader('app_theme', importlib.machinery.SourceFileLoader('app_theme', str(ROOT / 'bin/theme')))
theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)


def test_switch_replaces_old_base_and_keeps_user_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(theme, 'CFG', str(tmp_path))
    path = tmp_path / 'VSCodium/User/settings.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'workbench.colorTheme': 'Catppuccin Mocha', 'editor.fontSize': 17,
                               'workbench.colorCustomizations': {'custom.extensionColor': '#123456'}}))
    for name in ('catppuccin_mocha', 'gruvbox'):
        data = json.loads((ROOT / 'themes' / (name + '.json')).read_text())
        theme.gen_vscode(data['roles'], data.get('dark', True))
    result = json.loads(path.read_text())
    assert result['workbench.colorTheme'] == 'Default Dark Modern'
    assert result['editor.fontSize'] == 17
    assert result['workbench.colorCustomizations']['custom.extensionColor'] == '#123456'
    assert result['workbench.colorCustomizations']['editorGroupHeader.tabs.background'] == data['roles']['bg_alt']
    assert result['editor.tokenColorCustomizations']['strings'] == data['roles']['ansi_green']


def test_firefox_switch_keeps_valid_cache_and_no_stale_css(tmp_path, monkeypatch):
    monkeypatch.setattr(theme, 'HOME', str(tmp_path))
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'cache'))
    monkeypatch.setattr(theme.shutil, 'which', lambda _: '/installed/pywalfox')
    profile = tmp_path / '.mozilla/firefox/test.default-release'
    profile.mkdir(parents=True)
    for name in ('catppuccin_mocha', 'gruvbox'):
        data = json.loads((ROOT / 'themes' / (name + '.json')).read_text())
        theme.gen_firefox(data['roles'], data.get('dark', True), name)
    cache = json.loads((tmp_path / 'cache/wal/colors.json').read_text())
    assert cache['wallpaper']
    assert cache['theme_engine']['name'] == 'gruvbox'
    assert cache['colors']['color0'] == data['roles']['bg']
    assert cache['colors']['color10'] == data['roles']['accent']
    assert '#' not in (profile / 'chrome/userChrome.css').read_text()
