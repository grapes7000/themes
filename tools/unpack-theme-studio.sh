#!/usr/bin/env bash
# Reconstruct the reviewable Theme Studio source bundle committed in dist/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$ROOT/.theme-studio-unpacked}"
EXPECTED_SHA256="2a884fd2de7b95fca7cbc5ed2c3e295f83c304b15ee6e75c9e00eb343821fe4a"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

mkdir -p "$DEST"
cat "$ROOT"/dist/theme-studio-src.tar.gz.b64.part* | base64 --decode > "$TMP"
ACTUAL_SHA256="$(sha256sum "$TMP" | awk '{print $1}')"
if [[ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]]; then
    echo "Theme Studio bundle checksum mismatch" >&2
    echo "expected: $EXPECTED_SHA256" >&2
    echo "actual:   $ACTUAL_SHA256" >&2
    exit 1
fi

tar -xzf "$TMP" -C "$DEST"
for required in theme_schema.py theme_preview.py theme_components.py theme_tui_widgets.py theme_tui.py tests/test_theme_studio.py THEME-STUDIO.md Theme-Studio-TUI-Design-Plan.md; do
  [[ -e "$DEST/$required" ]] || { echo "Missing extracted file: $required" >&2; exit 1; }
done

# The bundled Theme Studio predates the standalone engine's ownership rules.
# Its generic apply_all() includes component renderers that rewrite files the
# canonical base-theme generators already own:
#
#   prompt  -> ~/.config/theme-engine/generated/starship.toml
#   windows -> ~/.config/hypr/generated/theme.conf
#
# On a normal `theme <name>` switch those second writes changed prompt geometry
# and replaced the theme's own Hyprland border/highlight/style with generic
# Theme Studio component defaults. Both renderers remain available when a
# caller explicitly requests those components; they are only excluded from an
# implicit "apply every component" operation.
python3 - "$DEST/theme_components.py" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = '    selected = names or list(PLUGINS)\n'
new = '    selected = names if names is not None else [name for name in PLUGINS if name not in {"prompt", "windows"}]\n'
if old not in text:
    raise SystemExit("Theme Studio compatibility patch failed: apply_all selector was not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

echo "Theme Studio source unpacked to: $DEST"
