# themes

A portable, JSON-driven **theme engine** for a Wayland/Hyprland desktop. One
command re-skins **Hyprland + Waybar + kitty + starship + Neovim** at once — colors,
blur, shadows, corner radius, gaps *and* a matching generated wallpaper — all
from a single `theme.json` per theme.

**28 themes included.** Each carries its own look-and-feel, not just colors:
sharp themes get tight gaps and no blur; glassy themes get heavy blur and big
radius; light themes get subtle shadows.

**New here? Start with the [TUTORIAL](TUTORIAL.md).**

---

## The idea

Every theme is one file: `themes/<name>.json`. It has two blocks:

- **`roles`** — semantic colors (`bg`, `accent`, `urgent`, ANSI palette, …).
- **`style`** — the *feel*: `corner_radius`, `blur_strength`, `shadow_*`,
  `gaps`, `border_width`, `opacity`, …

Running `theme <name>` reads that file and **generates** the per-app config:

```
themes/<name>.json ──► ~/.config/hypr/generated/theme.conf     (borders, blur, shadow, rounding)
                  ├──► ~/.config/waybar/generated/theme.css     (@define-color …)
                  ├──► ~/.config/kitty/generated/theme.conf      (bg/fg + 16 ANSI colors)
                  ├──► ~/.config/starship.toml                   (prompt palette)
                  ├──► ~/.config/nvim/lua/generated_theme.lua  (Neovim colorscheme)
                  └──► ~/.config/hypr/wallpapers/<name>.png       (via wallgen)
```
…then live-reloads each app. Nothing under `generated/` is hand-edited.

Full schema: **[docs/THEME-FORMAT.md](docs/THEME-FORMAT.md)**.

---

## Install

```sh
git clone <this-repo-url> ~/themes
cd ~/themes
./install.sh          # copies themes/ + wallpapers/ into ~/.config/hypr, bin/ into ~/.local/bin
theme catppuccin_mocha
```
`install.sh` detects your desktop (Hyprland / KDE / XFCE / GNOME-family) and
writes a matching `~/.config/theme-engine/targets.conf` the first time it
runs, enabling only the targets whose apps it actually finds on `PATH`. It
won't touch that file again once it exists — edit it by hand to add/remove
targets later (full list: [docs/DE-THEMING.md](docs/DE-THEMING.md)).
Requires `python-pillow` for wallgen (`sudo pacman -S python-pillow`). The
generators are pure Python 3 + Pillow — no other deps.

Make sure `~/.local/bin` is on your PATH (`fish_add_path -g ~/.local/bin` for fish).

---

## Commands

| Command | Description |
|---|---|
| `theme` | List all themes (marks the active one with `*`) |
| `theme <name>` | Switch theme — regenerate everything + live reload |
| `theme --list` | Bare list of names (for scripting) |
| `theme-new <name>` | Create a new theme, scaffolded from `catppuccin_mocha` |
| `theme-new <name> --from <base>` | …scaffold from a different theme |
| `theme-new <name> --edit` | …and open it in `$EDITOR` |
| `theme-menu` | Pick a theme with a wofi menu |
| `wallgen` | Regenerate **all** wallpapers |
| `wallgen <name>` | Regenerate one |
| `wallgen <name> --set` | Regenerate one and set it live |

---

## The 28 themes

**Dark:** catppuccin_mocha · catppuccin_macchiato · catppuccin_frappe ·
dracula · tokyonight · tokyonight-storm · everforest-dark · kanagawa ·
kanagawa-wave · onedark · material · nord · gruvbox · monokai · solarized-dark ·
hacker-pink · y2k

**Light:** catppuccin_latte · dracula-light · tokyonight-day · everforest-light ·
material-lighter · gruvbox-light · solarized-light · cappuccino · cyber-green

**Specials:** `ios-glassy` (frosted-glass morphism — heavy blur, big radius) ·
`vintage-mac` (retro boxy — no blur, small radius) · `y2k` (sharp, neon,
dramatic shadows)

---

## Make your own

```sh
theme-new synthwave --from tokyonight --edit
# edit roles{} colors + style{} feel, save
theme synthwave          # apply it (auto-generates a matching wallpaper)
```

The `wallgen` tool paints large, softly-blurred blobs from a theme's accent
colors over a gradient background — deterministic per theme name, so a given
theme always produces the same wallpaper.

---

## Using pieces standalone

- **`wallgen`** is generic: give it any `theme.json` with a `roles` block and it
  emits a 2560×1440 wallpaper. Useful outside Hyprland entirely.
- The **`theme.json` format** is a portable palette description — you can target
  new apps by adding a `gen_*` function to `bin/theme`.

---

## Attribution

Palettes adapted from their upstream projects, all under permissive licenses:
[Catppuccin](https://github.com/catppuccin), [Dracula](https://draculatheme.com),
[Nord](https://nordtheme.com), [Gruvbox](https://github.com/morhetz/gruvbox),
[Tokyo Night](https://github.com/enkia/tokyo-night-vscode-theme),
[Everforest](https://github.com/sainnhe/everforest),
[Kanagawa](https://github.com/rebelot/kanagawa.nvim),
[Solarized](https://ethanschoonover.com/solarized/),
[One Dark](https://github.com/atom/one-dark-syntax),
[Monokai](https://monokai.pro), Material. `hacker-pink`, `y2k`, `cappuccino`,
`cyber-green`, `ios-glassy`, `vintage-mac` are original.
