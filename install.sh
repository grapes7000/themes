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

has() { command -v "$1" >/dev/null 2>&1; }

# Detect the running desktop so targets.conf only enables what's actually
# usable on this machine -- a fresh clone on KDE should not default to
# Hyprland-only targets (and vice versa).
detect_de() {
    if [ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ] || has hyprctl; then
        echo hyprland
    elif [ -n "${KDE_FULL_SESSION:-}" ] || [ "${XDG_CURRENT_DESKTOP:-}" = "KDE" ] || has plasmashell; then
        echo kde
    elif [ "${XDG_CURRENT_DESKTOP:-}" = "XFCE" ] || has xfce4-session; then
        echo xfce
    elif [ "${XDG_CURRENT_DESKTOP:-}" = "X-Cinnamon" ] || [ "${XDG_CURRENT_DESKTOP:-}" = "MATE" ] \
         || [ "${XDG_CURRENT_DESKTOP:-}" = "GNOME" ] || has cinnamon-session || has mate-session || has gnome-shell; then
        echo gtk-de
    else
        echo unknown
    fi
}

# emit "$1" uncommented if binary "$2" is on PATH, else commented out
opt() { has "$2" && echo "$1" || echo "# $1"; }

write_targets_conf() {
    local de="$1" out="$CFG/theme-engine/targets.conf"
    {
        echo "# Enabled theme targets (one per line). Comment out to disable."
        echo "# Auto-picked at install for detected desktop: $de."
        echo "# Edit freely -- install.sh won't touch this file again once it exists."
        echo "# Full option list & what each target does: docs/DE-THEMING.md"
        case "$de" in
            hyprland)
                echo hypr
                opt waybar waybar
                opt kitty kitty
                opt starship starship
                opt nvim nvim
                opt wallpaper hyprpaper
                opt wofi wofi
                has wofi || opt rofi rofi
                opt dunst dunst
                opt hyprlock hyprlock
                echo "# kde"
                echo "# oomox"
                echo "# gtk"
                echo "# xfce"
                ;;
            kde)
                opt kitty kitty
                opt starship starship
                opt nvim nvim
                opt kde plasma-apply-colorscheme
                echo "# hypr"
                echo "# waybar"
                echo "# wallpaper"
                echo "# wofi"
                echo "# rofi"
                echo "# dunst"
                echo "# hyprlock"
                echo "# oomox"
                echo "# gtk"
                echo "# xfce"
                ;;
            xfce)
                opt kitty kitty
                opt starship starship
                opt nvim nvim
                echo xfce
                if has oomox-cli; then echo oomox; else echo "# oomox"; echo gtk; fi
                echo "# hypr"
                echo "# waybar"
                echo "# wallpaper"
                echo "# wofi"
                echo "# rofi"
                echo "# dunst"
                echo "# hyprlock"
                echo "# kde"
                ;;
            gtk-de)
                opt kitty kitty
                opt starship starship
                opt nvim nvim
                if has oomox-cli; then echo oomox; else echo "# oomox"; echo gtk; fi
                echo "# hypr"
                echo "# waybar"
                echo "# wallpaper"
                echo "# wofi"
                echo "# rofi"
                echo "# dunst"
                echo "# hyprlock"
                echo "# kde"
                echo "# xfce"
                ;;
            *)
                opt kitty kitty
                opt starship starship
                opt nvim nvim
                echo "# hypr"
                echo "# waybar"
                echo "# wallpaper"
                echo "# wofi"
                echo "# rofi"
                echo "# dunst"
                echo "# hyprlock"
                echo "# kde"
                echo "# oomox"
                echo "# gtk"
                echo "# xfce"
                ;;
        esac
        echo "# obsidian=~/Documents/Obsidian Vault"
        echo "# firefox"
    } > "$out"
}

mkdir -p "$CFG/theme-engine"
if [ ! -f "$CFG/theme-engine/targets.conf" ]; then
    de="$(detect_de)"
    write_targets_conf "$de"
    echo "Detected desktop: $de -- wrote $CFG/theme-engine/targets.conf (edit anytime)."
fi
echo "Installed $(ls "$REPO"/themes/*.json | wc -l) themes + generators."
echo "Ensure ~/.local/bin is on PATH, then run:  theme <name>"
echo "wallgen needs python-pillow:  sudo pacman -S python-pillow"
