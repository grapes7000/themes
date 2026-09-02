# Starship layout styles

The theme engine now separates **desktop palette** from **prompt layout**. Changing the desktop theme recolors the active Starship layout; changing the Starship layout does not change the desktop theme.

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

`theme starship <name>` is a shorthand for `theme starship use <name>`. `theme starship` by itself regenerates the active layout. `theme starship edit` opens the detailed TUI editor.

The selected layout and detailed prompt preferences are stored in `~/.config/theme-engine/starship.json`. The generated prompt remains `~/.config/starship.toml` and is still recolored from the active theme roles.

## Layouts

- **workspace** — the original two-line Powerline layout, expanded with a short commit hash, matching Git tag, remote tracking branch, Git operation state, counted working-tree status, and added/deleted line metrics.
- **minimal** — directory + branch + useful Git state only. Battery, time, jobs, language, cloud, and container context are off by default. Failed command status and slow command duration can still appear on the right.
- **hud** — a one-line information dashboard using Starship's `fill` module to bridge workspace/context information to status, battery, and time across the available terminal width.
- **neon** — a transparent variant of the workspace prompt. It keeps Git/dev context but trades filled Powerline blocks for thin separators and semantic accent colors.
- **operator** — a repo-focused console. It adds the age of the most recent commit and an optional project status signal, then keeps dev/container/cloud context on a separate line.

## Operator project status

`operator` checks for a non-empty `.starship-status` file at the Git repository root. If present, its contents are shown as a compact project signal.

For example:

```bash
echo 'tests:pass' > .starship-status
```

or:

```bash
echo 'agent:working' > .starship-status
```

This deliberately keeps expensive work outside prompt rendering. Tests, CI, agents, or build scripts can update the tiny file; Starship only reads the cached result.

## Performance

The built-in Git modules provide branch, commit/tag, state, status, and diff metrics. The `operator` layout adds two lightweight custom commands: a local `git log -1` for commit age and a read of `.starship-status` when that file exists. The layout uses a slightly higher Starship `command_timeout` than the other styles to accommodate those local checks without allowing long-running prompt hooks.
