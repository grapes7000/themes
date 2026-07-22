# Theme Engine — Tutorial

A quick, practical guide to using the theme system day-to-day.

---

## 1. Switch themes

```sh
theme                 # list all themes (the active one is marked *)
theme dracula         # switch instantly — reskins every enabled app + wallpaper
theme --list          # bare list (for scripts)
```

In Hyprland you can also press **Super+T** for a wofi picker, or run `theme-menu`.

Each switch regenerates and live-reloads Hyprland, Waybar, kitty, starship,
Neovim, wofi, rofi, dunst, hyprlock — and sets a matching wallpaper.

---

## 2. Make your own theme

```sh
theme-new synthwave --from tokyonight --edit
```

That copies an existing theme to `~/.config/hypr/themes/synthwave.json` and opens
it. Edit two blocks:

- **`roles`** — the colors (`bg`, `text`, `accent`, `accent2`, `urgent`, the ANSI
  set, …). At minimum set `bg`, `bg_alt`, `text`, `text_dim`, `focus`, `accent`,
  `accent2`, `urgent`.
- **`style`** — the *feel*: `corner_radius`, `blur_on`/`blur_strength`,
  `shadow_on`/`shadow_radius`/`shadow_opacity`, `gaps`, `border_width`,
  `opacity`. Sharp look = `corner_radius:0`, `blur_on:"false"`. Glassy = big
  radius + high blur.

Then apply it (also generates a matching wallpaper):

```sh
theme synthwave
```

Full field reference: [docs/THEME-FORMAT.md](docs/THEME-FORMAT.md).

---

## 3. Wallpapers

Wallpapers are generated from each theme's colors (soft blurred blobs):

```sh
wallgen               # regenerate all
wallgen synthwave     # just one
wallgen synthwave --set   # regenerate + set it live
```

Needs `python-pillow`.

---

## 4. Choose which apps get themed

Edit `~/.config/theme-engine/targets.conf` — one target per line; comment out to
disable. Some take a value:

```
hypr
waybar
kitty
wofi
rofi
dunst
hyprlock
nvim
starship
wallpaper
# obsidian=~/Documents/Obsidian Vault
# firefox
# --- host desktop targets ---
# kde
# gtk
# xfce
```

Only listed targets are touched. See
[docs/DE-THEMING.md](docs/DE-THEMING.md) for what each one does and the
desktop-environment (KDE/GTK/XFCE) options.

---

## 5. Undo everything

```sh
theme-uninstall
```

Removes generated files, strips the injected `@import` lines (restoring
backups), and reverts desktop-environment state. Your original configs are left
as they were.

---

## 6. Handy extras

- `shortcuts` — print the full keybind + command cheat sheet (Hyprland:
  **Super+Shift+?**).
- **Super+B** — themed Bitwarden picker (needs `rbw` + `rofi-rbw`; see the repo
  README).
- Waybar shows a VPN indicator: 🔒 + VPN IP when protected, ⚠ + exposed IP when
  off.

---

## Same engine on another machine

The engine is portable. On any machine: install the repo (`./install.sh`), put a
`targets.conf` listing that machine's apps (e.g. a Linux Mint host might use
`kde, gtk, xfce, kitty, nvim, starship`), then `theme <name>`. No Hyprland
required for the non-Hyprland targets.
