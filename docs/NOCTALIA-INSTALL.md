# Noctalia-safe installation

Use the dedicated installer on systems where Noctalia replaces Waybar, Wofi,
Dunst, Hyprlock, and Eww shell components.

```bash
bash ./install-noctalia.sh --dry-run
bash ./install-noctalia.sh
```

The installer does **not** install packages, edit shell startup files, change
Noctalia settings, import generated files into app configs, or apply a theme.
It installs Theme Studio and its generators, copies theme JSON files and
wallpapers, and creates a minimal `~/.config/theme-engine/targets.conf` only
when that file does not already exist.

The default Noctalia-safe targets are:

```text
hypr
kitty
starship
nvim
wallpaper
```

Waybar, Wofi/Rofi, Dunst, Hyprlock, and the Eww homepage remain disabled because
Noctalia supplies those shell surfaces. Firefox and Obsidian remain commented
until ownership is chosen explicitly, preventing Noctalia templates and Theme
Engine generators from writing the same app configuration.

## Rollback

Every installation records each created or replaced destination under:

```text
~/.local/state/theme-engine/install-snapshots/<timestamp>/
```

Preview the latest rollback:

```bash
theme-install-undo --dry-run
```

Restore the latest installation snapshot:

```bash
theme-install-undo
```

List snapshots or restore a specific one:

```bash
theme-install-undo --list
theme-install-undo --snapshot 20260804-013700
```

Rollback restores files exactly as they existed before the installer ran and
removes files that did not previously exist. It does not undo a theme applied
later with `theme <name>`; application-level changes remain covered by the
existing `theme-uninstall` command and each generator's backups.

## Ownership rule

Only one system should own each target. A recommended starting split is:

- Theme Engine: Hyprland effects, Kitty, Starship, Neovim, wallpaper.
- Noctalia: shell UI, GTK3/GTK4, Qt/KColorScheme, VSCodium, and other community templates.

Enable Firefox or Obsidian in `targets.conf` only after disabling the equivalent
Noctalia template.
