#!/usr/bin/env bash
# Safe, reversible Theme Engine install profile for Noctalia v5.
set -euo pipefail

_src="${BASH_SOURCE[0]-}"
if [[ -z "$_src" || ! -f "$_src" ]]; then
  echo "Run install-noctalia.sh from a cloned themes repository." >&2
  exit 2
fi

REPO="$(cd "$(dirname "$_src")" && pwd)"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}"
STAMP="$(date +%Y%m%d-%H%M%S)"
SNAPSHOT="$STATE/theme-engine/noctalia-installs/$STAMP"
DRY_RUN=0
APPLY_THEME=""

usage() {
  cat <<'EOF'
Usage: ./install-noctalia.sh [--dry-run] [--apply THEME]

Installs Theme Engine for Noctalia without installing packages or modifying
shell startup files. Everything touched is captured in one rollback snapshot.
Undo with: theme-noctalia-uninstall restore
EOF
}

while (($#)); do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --apply) shift; APPLY_THEME="${1:?--apply needs a theme name}" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
command -v noctalia >/dev/null || { echo "Noctalia v5 was not found on PATH" >&2; exit 1; }

STUDIO_TMP="$(mktemp -d)"
PATHS_FILE="$(mktemp)"
trap 'rm -rf "$STUDIO_TMP" "$PATHS_FILE"' EXIT
bash "$REPO/tools/unpack-theme-studio.sh" "$STUDIO_TMP" >/dev/null

# Exact locations that install/apply can touch. The snapshot records absence too,
# so rollback removes newly-created files and restores pre-existing ones byte-for-byte.
{
  echo "$HOME/.local/bin/theme"
  echo "$HOME/.local/bin/theme-studio"
  echo "$HOME/.local/bin/theme-legacy"
  for name in theme-new theme-menu theme-uninstall wallgen starship-config theme-pywalfox theme-stylus theme-from-image theme-noctalia theme-noctalia-uninstall; do
    echo "$HOME/.local/bin/$name"
  done
  for name in theme_starship.py theme_effects.py theme_homepage.py theme_editor.py theme_runtime.py theme_schema.py theme_preview.py theme_components.py theme_tui_widgets.py theme_tui.py; do
    echo "$HOME/.local/bin/$name"
  done
  echo "$HOME/.config/hypr/themes"
  echo "$HOME/.config/hypr/wallpapers"
  echo "$HOME/.config/hypr/generated"
  echo "$HOME/.config/hypr/hyprland.conf"
  echo "$HOME/.config/hypr/hyprpaper.conf"
  echo "$HOME/.config/theme-engine/targets.conf"
  echo "$HOME/.config/kitty/kitty.conf"
  echo "$HOME/.config/kitty/generated"
  echo "$HOME/.config/starship.toml"
  echo "$HOME/.config/nvim/lua/generated_theme.lua"
  echo "$HOME/.config/VSCodium/User/settings.json"
  echo "$HOME/.config/gtk-3.0/gtk.css"
  echo "$HOME/.config/gtk-4.0/gtk.css"
  echo "$HOME/.config/qt5ct/qt5ct.conf"
  echo "$HOME/.config/qt5ct/colors/ThemeEngine.conf"
  echo "$HOME/.config/qt6ct/qt6ct.conf"
  echo "$HOME/.config/qt6ct/colors/ThemeEngine.conf"
  echo "$HOME/.config/noctalia/palettes/theme-engine-active.json"
  echo "$HOME/.local/state/noctalia/settings.toml"
  echo "$HOME/.local/state/theme-engine/noctalia-bridge.json"
  echo "${XDG_CACHE_HOME:-$HOME/.cache}/wal/colors.json"
  find "$HOME" -maxdepth 4 -type d -name .obsidian -print 2>/dev/null | while read -r dir; do
    echo "$dir/appearance.json"
    echo "$dir/snippets/theme-engine.css"
  done
  for root in "$HOME/.mozilla/firefox" "$HOME/.floorp" "$HOME/.librewolf" "$HOME/.zen" "$HOME/.waterfox"; do
    [[ -d "$root" ]] || continue
    find "$root" -maxdepth 3 -type d -name '*.default*' -print 2>/dev/null | while read -r profile; do
      echo "$profile/user.js"
      echo "$profile/chrome/userChrome.css"
    done
  done
} | awk 'NF && !seen[$0]++' > "$PATHS_FILE"

if ((DRY_RUN)); then
  echo "No changes made. The installer would snapshot these paths:"
  sed 's/^/  /' "$PATHS_FILE"
  echo
  echo "It would then install commands/themes, write a Noctalia-safe targets.conf,"
  echo "add one generated-theme source line to hyprland.conf, and disable overlapping"
  echo "Noctalia app templates. It never installs packages."
  exit 0
fi

python3 "$REPO/bin/theme-noctalia-uninstall" snapshot \
  --paths-file "$PATHS_FILE" --snapshot "$SNAPSHOT" >/dev/null

echo "Rollback snapshot: $SNAPSHOT"
mkdir -p "$CFG/hypr/themes" "$CFG/hypr/wallpapers" "$CFG/hypr/generated" \
         "$CFG/theme-engine" "$HOME/.local/bin" "$HOME/.local/share/doc/theme-studio"
cp "$REPO"/themes/*.json "$CFG/hypr/themes/"
cp "$REPO"/wallpapers/*.png "$CFG/hypr/wallpapers/" 2>/dev/null || true

install -m755 "$REPO/bin/theme" "$HOME/.local/bin/theme-legacy"
install -m755 "$REPO/bin/theme-studio" "$HOME/.local/bin/theme"
install -m755 "$REPO/bin/theme-studio" "$HOME/.local/bin/theme-studio"
for name in theme-new theme-menu theme-uninstall wallgen starship-config theme-pywalfox theme-stylus theme-from-image; do
  install -m755 "$REPO/bin/$name" "$HOME/.local/bin/$name"
done
install -m755 "$REPO/bin/theme-noctalia" "$HOME/.local/bin/theme-noctalia"
install -m755 "$REPO/bin/theme-noctalia-uninstall" "$HOME/.local/bin/theme-noctalia-uninstall"
for name in theme_starship.py theme_effects.py theme_homepage.py theme_editor.py theme_runtime.py; do
  install -m644 "$REPO/bin/$name" "$HOME/.local/bin/$name"
done
for name in theme_schema.py theme_preview.py theme_components.py theme_tui_widgets.py theme_tui.py; do
  install -m644 "$STUDIO_TMP/$name" "$HOME/.local/bin/$name"
done
install -m644 "$STUDIO_TMP/THEME-STUDIO.md" "$HOME/.local/share/doc/theme-studio/README.md"

# Theme Engine owns deep app/compositor theming. No Eww/Dunst/Hyprlock
# targets are enabled because Noctalia owns those shell surfaces.
{
  echo '# Noctalia-safe Theme Engine targets. Restorable with theme-noctalia-uninstall.'
  echo hypr
  command -v kitty >/dev/null && echo kitty
  command -v starship >/dev/null && echo starship
  command -v nvim >/dev/null && echo nvim
  echo wallpaper
  echo gtk
  { [[ -d "$CFG/qt5ct" ]] || [[ -d "$CFG/qt6ct" ]]; } && echo qt
  [[ -d "$CFG/VSCodium/User" ]] && echo vscode
  echo firefox
  mapfile -t vaults < <(find "$HOME" -maxdepth 4 -type d -name .obsidian -printf '%h\n' 2>/dev/null | sort -u)
  if ((${#vaults[@]} == 1)); then
    echo "obsidian=${vaults[0]}"
  else
    echo '# obsidian=/path/to/your/vault'
  fi
} > "$CFG/theme-engine/targets.conf"

# Hyprland must import the generated compositor styling. Append a clearly-owned
# block only when it is missing; rollback restores the exact original file.
HYPRCONF="$CFG/hypr/hyprland.conf"
mkdir -p "$(dirname "$HYPRCONF")"
touch "$HYPRCONF"
if ! grep -Fq 'source = ~/.config/hypr/generated/theme.conf' "$HYPRCONF"; then
  cat >> "$HYPRCONF" <<'EOF'

# THEME-ENGINE-NOCTALIA-START
source = ~/.config/hypr/generated/theme.conf
# THEME-ENGINE-NOCTALIA-END
EOF
fi

# Prevent Noctalia from overwriting the apps Theme Engine now owns.
"$HOME/.local/bin/theme-noctalia" configure

if [[ -n "$APPLY_THEME" ]]; then
  "$HOME/.local/bin/theme" "$APPLY_THEME"
fi

echo
echo "Installed the Noctalia-safe Theme Engine profile."
echo "Apply: theme y2k"
echo "Undo everything: theme-noctalia-uninstall restore"
echo "Preview first next time: ./install-noctalia.sh --dry-run"
