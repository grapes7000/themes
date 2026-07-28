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
for required in theme_schema.py theme_preview.py theme_waybar.py theme_components.py theme_tui_widgets.py theme_tui.py tests/test_theme_studio.py THEME-STUDIO.md Theme-Studio-TUI-Design-Plan.md; do
  [[ -e "$DEST/$required" ]] || { echo "Missing extracted file: $required" >&2; exit 1; }
done

echo "Theme Studio source unpacked to: $DEST"
