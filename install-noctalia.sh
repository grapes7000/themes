#!/usr/bin/env bash
# Safe, reversible Theme Engine installer for Noctalia + Hyprland.
# Installs files only; never installs packages, edits shell startup files,
# changes Noctalia settings, or applies a theme automatically.
set -euo pipefail

_src="${BASH_SOURCE[0]-}"
if [ -z "$_src" ] || [ ! -f "$_src" ]; then
    printf 'Downloading themes...\n'
    _tmpdir="$(mktemp -d)"
    trap 'rm -rf "$_tmpdir"' EXIT
    git clone --depth 1 https://github.com/grapes7000/themes.git "$_tmpdir/themes"
    bash "$_tmpdir/themes/install-noctalia.sh" "$@"
    exit $?
fi

REPO="$(cd "$(dirname "$_src")" && pwd)"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"
STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
STAMP="$(date +%Y%m%d-%H%M%S)"
SNAPSHOT="$STATE_HOME/theme-engine/install-snapshots/$STAMP"
FILES_DIR="$SNAPSHOT/files"
MANIFEST="$SNAPSHOT/manifest.tsv"
DRY_RUN=0

usage() {
    cat <<'EOF'
Usage: ./install-noctalia.sh [--dry-run]

Safe Noctalia install mode:
  - installs Theme Studio, generators, themes, and wallpapers
  - never installs packages
  - never edits Noctalia, Hyprland, Kitty, shell, or app configs
  - never applies a theme automatically
  - creates a timestamped rollback snapshot
  - creates a minimal Noctalia-friendly targets.conf only when missing

Undo the latest install with:
  theme-install-undo
EOF
}

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $arg" >&2; usage >&2; exit 2 ;;
    esac
done

run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '+ '
        printf '%q ' "$@"
        printf '\n'
    else
        "$@"
    fi
}

snapshot_path() {
    local path="$1" rel
    rel="${path#/}"
    printf '%s/%s' "$FILES_DIR" "$rel"
}

record_destination() {
    local dest="$1" backup
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        backup="$(snapshot_path "$dest")"
        run mkdir -p "$(dirname "$backup")"
        run cp -a "$dest" "$backup"
        [ "$DRY_RUN" -eq 1 ] || printf 'restore\t%s\t%s\n' "$dest" "$backup" >> "$MANIFEST"
    else
        [ "$DRY_RUN" -eq 1 ] || printf 'remove\t%s\t-\n' "$dest" >> "$MANIFEST"
    fi
}

install_one() {
    local src="$1" dest="$2" mode="$3"
    record_destination "$dest"
    run mkdir -p "$(dirname "$dest")"
    run install -m "$mode" "$src" "$dest"
}

copy_one() {
    local src="$1" dest="$2"
    record_destination "$dest"
    run mkdir -p "$(dirname "$dest")"
    run cp "$src" "$dest"
}

if [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$FILES_DIR"
    : > "$MANIFEST"
    cat > "$SNAPSHOT/metadata" <<EOF
mode=noctalia
created=$STAMP
repo=$REPO
EOF
fi

# Theme data. Record each destination independently so rollback is exact.
for src in "$REPO"/themes/*.json; do
    copy_one "$src" "$CFG/hypr/themes/$(basename "$src")"
done
for src in "$REPO"/wallpapers/*.png; do
    [ -e "$src" ] || continue
    copy_one "$src" "$CFG/hypr/wallpapers/$(basename "$src")"
done

STUDIO_TMP="$(mktemp -d)"
trap 'rm -rf "$STUDIO_TMP"' EXIT
bash "$REPO/tools/unpack-theme-studio.sh" "$STUDIO_TMP" >/dev/null

install_one "$REPO/bin/theme" "$HOME/.local/bin/theme-legacy" 755
install_one "$REPO/bin/theme-studio" "$HOME/.local/bin/theme" 755
for t in theme-new theme-menu theme-uninstall theme-install-undo wallgen starship-config theme-pywalfox theme-stylus theme-from-image; do
    install_one "$REPO/bin/$t" "$HOME/.local/bin/$t" 755
done
for module in theme_starship.py theme_effects.py theme_homepage.py theme_editor.py theme_runtime.py; do
    install_one "$REPO/bin/$module" "$HOME/.local/bin/$module" 644
done
for module in theme_schema.py theme_preview.py theme_waybar.py theme_components.py theme_tui_widgets.py theme_tui.py; do
    install_one "$STUDIO_TMP/$module" "$HOME/.local/bin/$module" 644
done
install_one "$STUDIO_TMP/THEME-STUDIO.md" "$HOME/.local/share/doc/theme-studio/README.md" 644
install_one "$STUDIO_TMP/Theme-Studio-TUI-Design-Plan.md" "$HOME/.local/share/doc/theme-studio/Design-Plan.md" 644
install_one "$REPO/docs/NOCTALIA-INSTALL.md" "$HOME/.local/share/doc/theme-studio/NOCTALIA-INSTALL.md" 644

TARGETS="$CFG/theme-engine/targets.conf"
if [ ! -e "$TARGETS" ]; then
    record_destination "$TARGETS"
    run mkdir -p "$(dirname "$TARGETS")"
    if [ "$DRY_RUN" -eq 0 ]; then
        cat > "$TARGETS" <<'EOF'
# Noctalia-safe Theme Engine targets.
# Noctalia owns its bar, widgets, launcher, notifications, lock screen,
# GTK/Qt templates, and community app templates unless you choose otherwise.
hypr
kitty
starship
nvim
wallpaper

# Optional: enable only after deciding which system owns each app.
# firefox
# obsidian=~/Documents/Obsidian Vault

# Intentionally disabled with Noctalia:
# waybar
# wofi
# rofi
# dunst
# hyprlock
# homepage
EOF
    fi
fi

if [ "$DRY_RUN" -eq 1 ]; then
    echo
    echo "Dry run only: no files were changed and no rollback snapshot was created."
    exit 0
fi

ln -sfn "$SNAPSHOT" "$STATE_HOME/theme-engine/install-snapshots/latest"

echo "Installed Theme Engine in Noctalia-safe mode."
echo "No packages were installed, no configs were imported, and no theme was applied."
echo "Rollback snapshot: $SNAPSHOT"
echo
echo "Preview available themes: theme --list"
echo "Apply later:              theme <name>"
echo "Undo this installation:  theme-install-undo"
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo
    echo "Fish PATH setup (one time): fish_add_path -g ~/.local/bin"
fi
