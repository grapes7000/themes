# Theming more apps & desktop environments

The engine is **opt-in per target** via `~/.config/theme-engine/targets.conf`
(one target per line; `key=value` for those that need a path). Only listed
targets are touched. Everything is written to dedicated generated files that the
app `@import`s — originals are backed up and `theme-uninstall` reverts it all.

`install.sh` auto-generates this file the first install, based on your
detected desktop (Hyprland/KDE/XFCE/GNOME-family) and which app binaries are
on `PATH` — e.g. a KDE machine gets `kitty` + `kde` enabled, not the
Hyprland-only targets. It's a starting point, not a ceiling: uncomment any
other line below to enable it by hand.

## Targets

| Target | App | Notes |
|---|---|---|
| hypr, waybar, kitty, starship, nvim, wallpaper | core Hyprland desktop | live reload |
| zsh | oh-my-zsh | generates a custom `theme-engine` zsh-theme + sets `ZSH_THEME` once (won't fight a later manual switch). Open a new terminal or run `exec zsh` to see it — no live reload |
| wofi / rofi | launchers | `@import` a generated colors file. rofi also themes **rofi-rbw** (Bitwarden) and every rofi menu |
| dunst | notifications | full `dunstrc` generated (original backed up) |
| hyprlock | lock screen | live |
| obsidian=`<vault>` | Obsidian | CSS snippet using Obsidian CSS vars; hot-reloads. Per vault |
| firefox | Firefox chrome | `userChrome.css` (toolbar only); needs a restart; profile must exist |
| kde | KDE Plasma | `.colors` scheme + `plasma-apply-colorscheme` — full & clean |
| oomox | GTK DEs (Cinnamon/XFCE/MATE/GNOME apps) | generates an oomox preset, builds+installs a full GTK theme via `oomox-cli`, applies via gsettings/xfconf |
| gtk | GTK fallback (no oomox) | `@define-color` overrides in gtk.css — partial recolor |
| xfce | xfce4-terminal | color scheme |

## Pywal and pywalfox compatibility

`theme-pywalfox [theme-name]` exports any theme to the standard
`$XDG_CACHE_HOME/wal/colors.json` format and runs `pywalfox update` when the
native host is installed. With no theme name it exports the currently active
theme.

```sh
theme catppuccin_mocha
theme-pywalfox

# Or export another theme without applying it first:
theme-pywalfox nord
```

The compatibility cache includes an ordered 16-color palette, special colors,
and the wallpaper path required by pywalfox. It does not change the source theme
or apply a second desktop reload pipeline.

The planned automatic `pywal` target and image-to-theme work are documented in
[`PYWAL-INTEGRATION-PLAN.md`](PYWAL-INTEGRATION-PLAN.md).

## Non-invasive & reversible
- Nothing overwrites your own config; each app gains one `@import`/`@theme` line
  (backed up) or a separate generated file.
- `theme-uninstall` removes generated files, strips the import lines, restores
  backups, and reverts DE state (stock KDE scheme, reset GTK theme).

## oomox preset mapping (manual GUI equivalent)
`gen_oomox` maps: BG=bg, FG=text, MENU_BG=bg_alt, SEL_BG=**accent**, SEL_FG=bg,
ROUNDNESS=corner_radius, dark/light from the theme. In the GUI: pick **Materia**,
set Selection/accent to the theme accent, background to bg, foreground to text.
