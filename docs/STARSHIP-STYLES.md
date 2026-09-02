# Starship prompt layouts

The themes repo owns the Starship layout renderer. Every layout uses the active desktop theme's semantic colors, so changing desktop themes recolors the selected Starship layout without changing its geometry.

## Commands

```bash
theme starship list
theme starship current
theme starship use workspace
theme starship use minimal
theme starship use hud
theme starship use muted
theme starship use neon
theme starship use operator
```

The style name may also be used directly, for example `theme starship muted`. `theme starship edit` opens the detailed Starship TUI.

## Layouts

### workspace

The original known-good two-line filled Powerline prompt is preserved as the default. Its visible module order and geometry match the pre-switcher renderer: OS Nerd Font symbol / identity → directory → Git branch/state/status → development context, with transparent status, duration, jobs, battery, and time on the right.

### minimal

A quiet two-line prompt with only the directory and Git branch/status on the left. Battery, clock, jobs, language, container, and cloud modules are disabled by the preset. Failed-command status and slow-command duration can still appear on the right.

### hud

A compact dashboard. OS, directory, Git status, development context, and telemetry share one line, with Starship's `fill` module stretching a dotted bridge across unused terminal width. The prompt marker sits on the second line.

### muted

A calmer alternative to `workspace`. It keeps the same kind of Powerline segmentation, but the identity, directory, and Git blocks use the theme's neutral/background/text roles instead of alternating bright accent colors. Urgent states can still break through in the warning/error color.

### neon

A clean Powerline layout rather than the old `SYS / PATH / GIT` cyber labels. It derives two new colors from the active theme's `accent` and `accent2` hues, then increases their saturation and brightness. That means a brown/orange theme gets bright neon orange, a purple theme gets bright neon purple, a green theme gets bright neon green, etc. The colors are generated from the current theme rather than hardcoded.

### operator

A multi-line repo console with labeled `cwd`, `git`, and `env` rows. The Git row includes branch, commit, state/status, diff metrics, and a custom last-commit-age module. The environment row can display a cached project signal from `.starship-status` at the repository root.

Example:

```bash
echo 'tests:pass' > "$(git rev-parse --show-toplevel)/.starship-status"
```

This is intentionally a cached signal: Starship reads one short file instead of running a test suite or build on every prompt render.

## Original glyph preservation

`workspace` keeps the original Nerd Font code points used before the layout switcher. In particular, Arch/CachyOS uses `` and the Git branch symbol uses ``. The feature branch also migrates the accidentally zero-padded saved Git icon back to `` when reading the Starship profile.

## Theme color ownership

`~/.config/starship.toml` is the canonical generated Starship config. On installations whose `STARSHIP_CONFIG` points at `~/.config/theme-engine/generated/starship.toml`, the `theme` wrapper converts that managed path into a symlink to the canonical file. This prevents the mirror from going stale if a later desktop component blocks or times out during a full theme apply.

## Profile

The selected layout and user-tunable Starship options are stored in:

```text
~/.config/theme-engine/starship.json
```

Switching desktop color themes does not change this profile; switching Starship layouts does not change the desktop theme.
