# Noctalia v5 integration

This profile makes Theme Engine the authoritative renderer for deep app and
Hyprland styling while Noctalia remains the shell.

## Ownership

Theme Engine owns Hyprland effects, Kitty, Starship, Neovim, GTK, Qt,
VSCodium, Obsidian (when one vault is auto-detected), Firefox-family browsers,
and the wallpaper. Noctalia owns its bars, dock, launcher, notifications,
lockscreen, panels, and widgets.

The installer disables an overlapping Noctalia template only when the matching
Theme Engine target is enabled. Unrelated templates stay enabled and receive
the generated Theme Engine palette.

## Install safely

These commands work from Fish, Bash, and Zsh:

```bash
bash ./install-noctalia.sh --dry-run
bash ./install-noctalia.sh
```

The installer never installs packages and never edits shell startup files. It
creates a timestamped snapshot under:

```text
~/.local/state/theme-engine/noctalia-installs/
```

No theme is applied unless `--apply NAME` is passed.

## Apply

```bash
theme y2k
```

Theme Studio and the normal named-theme command both generate
`~/.config/noctalia/palettes/theme-engine-active.json`, select it as Noctalia's
custom palette, and apply the same source theme to the enabled deep-theme
targets. Waybar output is skipped when the `waybar` target is disabled.

## Undo

```bash
theme-noctalia-uninstall restore
```

Rollback restores the exact files captured before installation, removes files
that did not previously exist, and reloads Hyprland, Kitty, and Noctalia. The
snapshot is retained unless `--purge-backup` is supplied.

## Manual ownership changes

Edit:

```text
~/.config/theme-engine/targets.conf
```

Avoid enabling Waybar, Eww homepage, Dunst, or Hyprlock while Noctalia owns
those shell surfaces.
