"""Exercise the real installer and installed app generators in an isolated home."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstalledAppPalettes(unittest.TestCase):
    def test_installed_switch_and_upgrade(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / '.config'
            user = config / 'VSCodium/User/settings.json'
            user.parent.mkdir(parents=True)
            user.write_text(json.dumps({'workbench.colorTheme': 'Catppuccin Mocha', 'editor.fontSize': 17}))
            profile = home / '.mozilla/firefox/test.default-release'
            profile.mkdir(parents=True)
            targets = config / 'theme-engine/targets.conf'
            targets.parent.mkdir(parents=True)
            targets.write_text('firefox\nvscode\n')
            native = home / '.local/bin/pywalfox'
            native.parent.mkdir(parents=True)
            native.write_text('#!/bin/sh\nexit 0\n')
            native.chmod(0o755)
            env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(config),
                       XDG_CACHE_HOME=str(home / '.cache'),
                       XDG_DATA_HOME=str(home / '.local/share'),
                       XDG_STATE_HOME=str(home / '.local/state'),
                       PATH=str(native.parent) + ':/usr/bin:/bin')
            def run(*args):
                result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for iteration in range(2):
                run('bash', str(ROOT / 'install.sh'), '--targets', 'terminal')
                self.assertEqual(targets.read_text(), 'firefox\nvscode\n')
                self.assertEqual((native.parent / 'theme-legacy').read_bytes(), (ROOT / 'bin/theme').read_bytes())
                for name in ('catppuccin_mocha', 'gruvbox'):
                    run(str(native.parent / 'theme-legacy'), name)
                    roles = json.loads((ROOT / 'themes' / (name + '.json')).read_text())['roles']
                    cache = json.loads((home / '.cache/wal/colors.json').read_text())
                    self.assertTrue(cache['wallpaper'])
                    self.assertEqual(cache['theme_engine']['name'], name)
                    self.assertEqual(cache['colors']['color0'], roles['bg'])
                    self.assertEqual(cache['colors']['color10'], roles['accent'])
                    self.assertNotIn('!important', (profile / 'chrome/userChrome.css').read_text())
                    settings = json.loads(user.read_text())
                    self.assertEqual(settings['workbench.colorTheme'], 'Default Dark Modern')
                    self.assertEqual(settings['editor.fontSize'], 17)
                    self.assertEqual(settings['workbench.colorCustomizations']['panel.background'], roles['bg_alt'])
                    self.assertEqual(settings['editor.tokenColorCustomizations']['strings'], roles['ansi_green'])


if __name__ == '__main__':
    unittest.main()
