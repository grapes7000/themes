# Starship prompt layouts

The themes repo owns the Starship layout renderer. Every layout uses the active desktop theme's semantic colors, so changing desktop themes recolors the selected Starship layout without changing its geometry.

## Commands

```bash
theme starship list
theme starship current
theme starship use workspace
theme starship use minimal
theme starship use hud
theme starship use neon
theme starship use operator
```

The style name may also be used directly, for example `theme starship hud`. `theme starship edit` opens the detailed Starship TUI.

## Layouts

### workspace

The original known-good two-line filled Powerline prompt is preserved as the default. Its visible module order and geometry match the pre-switcher renderer: OS Nerd Font symbol / identity → directory → Git branch/state/status → development context, with transparent status, duration, jobs, battery, and time on the right. Richer commit-hash and diff-metric experiments live in the alternate layouts instead of changing `workspace`.

### minimal

A quiet two-line prompt with only the directory and Git branch/status on the left. Battery, clock, jobs, language, container, and cloud modules are disabled by the preset. Failed-command status and slow-command duration can still appear on the right.

### hud

A compact dashboard. OS, directory, Git status, development context, and telemetry share one line, with Starship's `fill` module stretching a dotted bridge across unused terminal width. The prompt marker sits on the second line.

### neon

A transparent cyber layout rather than a Powerline variant. The first line uses explicit `SYS`, `PATH`, and `GIT` sections with angular separators; development/container context lives on the second line. It uses the same active theme palette, but no filled Powerline blocks.

### operator

A multi-line repo console with labeled `cwd`, `git`, and `env` rows. The Git row includes branch, commit, state/status, diff metrics, and a custom last-commit-age module. The environment row can display a cached project signal from `.starship-status` at the repository root.

Example:

```bash
echo 'tests:pass' > "$(git rev-parse --show-toplevel)/.starship-status"
```

This is intentionally a cached signal: Starship reads one short file instead of running a test suite or build on every prompt render.

## Theme color ownership

`~/.config/starship.toml` is the canonical generated Starship config. On installations whose `STARSHIP_CONFIG` points at `~/.config/theme-engine/generated/starship.toml`, the `theme` wrapper converts that managed path into a symlink to the canonical file. This prevents the mirror from going stale if a later desktop component blocks or times out during a full theme apply.

## Profile

The selected layout and user-tunable Starship options are stored in:

```text
~/.config/theme-engine/starship.json
```

Switching desktop color themes does not change this profile; switching Starship layouts does not change the desktop theme.
