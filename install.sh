#!/usr/bin/env bash
# Install the theme engine: themes + wallpapers into ~/.config/hypr,
# generators into ~/.local/bin. Re-runnable.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"

mkdir -p "$CFG/hypr/themes" "$CFG/hypr/wallpapers" "$CFG/hypr/generated" "$HOME/.local/bin"
cp "$REPO"/themes/*.json         "$CFG/hypr/themes/"
cp "$REPO"/wallpapers/*.png      "$CFG/hypr/wallpapers/" 2>/dev/null || true
for t in theme theme-new theme-menu wallgen; do
    install -m755 "$REPO/bin/$t" "$HOME/.local/bin/$t"
done
mkdir -p "$CFG/theme-engine"
[ -f "$CFG/theme-engine/targets.conf" ] || cp "$REPO/targets.conf.example" "$CFG/theme-engine/targets.conf"
echo "Installed $(ls "$REPO"/themes/*.json | wc -l) themes + generators."
echo "Ensure ~/.local/bin is on PATH, then run:  theme <name>"
echo "wallgen needs python-pillow:  sudo pacman -S python-pillow"
