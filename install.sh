#!/usr/bin/env bash
# Install the theme engine: themes + wallpapers into ~/.config/hypr,
# generators into ~/.local/bin. Re-runnable.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="${XDG_CONFIG_HOME:-$HOME/.config}"

ensure_shell_path() {
    local file="$1" line='export PATH="$HOME/.local/bin:$PATH"'
    touch "$file"
    grep -Fqx "$line" "$file" || printf '\n%s\n' "$line" >> "$file"
}

mkdir -p "$CFG/hypr/themes" "$CFG/hypr/wallpapers" "$CFG/hypr/generated" "$HOME/.local/bin"
cp "$REPO"/themes/*.json         "$CFG/hypr/themes/"
cp "$REPO"/wallpapers/*.png      "$CFG/hypr/wallpapers/" 2>/dev/null || true
for t in theme theme-new theme-menu wallgen starship-config theme-pywalfox theme-stylus; do
    install -m755 "$REPO/bin/$t" "$HOME/.local/bin/$t"
done
install -m644 "$REPO/bin/theme_starship.py" "$HOME/.local/bin/theme_starship.py"
install -m644 "$REPO/bin/theme_effects.py" "$HOME/.local/bin/theme_effects.py"
install -m644 "$REPO/bin/theme_homepage.py" "$HOME/.local/bin/theme_homepage.py"
ensure_shell_path "$HOME/.zshrc"
ensure_shell_path "$HOME/.bashrc"

has() { command -v "$1" >/dev/null 2>&1; }

# Package name -> binary name, where they differ (pacman pkg "neovim" -> bin "nvim").
pkg_bin() { case "$1" in neovim) echo nvim ;; *) echo "$1" ;; esac; }

# Install whatever's missing among the tools this DE would enable, plus
# zsh + oh-my-zsh (not DE-specific). Always confirms before touching the
# system; never installs on a non-interactive run.
maybe_install_packages() {
    local de="$1"
    local want=(kitty starship neovim zsh)
    [ "$de" = hyprland ] && want+=(waybar wofi dunst hyprlock eww)

    local missing=()
    for pkg in "${want[@]}"; do
        has "$(pkg_bin "$pkg")" || missing+=("$pkg")
    done
    local need_omz=0
    [ -d "$HOME/.oh-my-zsh" ] || need_omz=1

    { [ ${#missing[@]} -eq 0 ] && [ "$need_omz" -eq 0 ]; } && return

    echo
    echo "Can install to fully match your terminal setup:"
    [ ${#missing[@]} -gt 0 ] && echo "  pacman:    ${missing[*]}"
    [ "$need_omz" -eq 1 ] && echo "  oh-my-zsh: via the official installer (ohmyzsh/ohmyzsh)"

    if [ ! -t 0 ]; then
        echo "Not an interactive terminal -- skipping. Re-run install.sh directly to install."
        return
    fi
    read -rp "Install now? [y/N] " reply
    case "$reply" in
        y|Y|yes|YES)
            if [ ${#missing[@]} -gt 0 ]; then
                sudo pacman -S --needed "${missing[@]}" || echo "pacman install failed -- continuing anyway."
            fi
            if [ "$need_omz" -eq 1 ]; then
                RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c \
                  "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" \
                  "" --unattended \
                  || echo "oh-my-zsh install failed -- continuing anyway."
            fi
            ;;
        *)
            echo "Skipped. Re-run install.sh anytime to retry."
            ;;
    esac
}

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
                opt zsh zsh
                opt wallpaper hyprpaper
                opt wofi wofi
                has wofi || opt rofi rofi
                opt dunst dunst
                opt hyprlock hyprlock
                opt homepage eww
                echo "# kde"
                echo "# oomox"
                echo "# gtk"
                echo "# xfce"
                ;;
            kde)
                opt kitty kitty
                opt starship starship
                opt nvim nvim
                opt zsh zsh
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
                opt zsh zsh
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
                opt zsh zsh
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
                opt zsh zsh
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
    maybe_install_packages "$de"
    write_targets_conf "$de"
    echo "Detected desktop: $de -- wrote $CFG/theme-engine/targets.conf (edit anytime)."
fi

echo "Installed $(ls "$REPO"/themes/*.json | wc -l) themes + generators."
echo "Added ~/.local/bin to zsh and bash startup files. Open a new shell, then run:"
echo "  Apply desktop theme:  theme <name>"
echo "  Update Firefox:       theme-pywalfox <name>"
echo "  Generate webpage CSS: theme-stylus <name> --open"
echo "wallgen needs python-pillow:  sudo pacman -S python-pillow"
