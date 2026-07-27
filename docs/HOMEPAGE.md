# Desktop Homepage Overlay

A transparent desktop overlay showing clock, theme info, workspaces,
system stats, and now-playing media. Powered by [Eww](https://github.com/elkowar/eww),
themed automatically from the engine's semantic color roles.

## Requirements

- Eww: `sudo pacman -S eww`
- Optional: `playerctl` for media widget, `socat` and `jq` for workspace events

## Quick Start

```sh
theme homepage on          # enable + start
theme homepage off         # stop + disable
theme homepage             # show status
theme homepage restart     # restart
theme homepage right       # move widgets to right side
theme homepage left        # move widgets to left side
```

The overlay starts automatically on `theme homepage on` and reloads its
colors whenever you switch themes with `theme <name>`.

## Widgets

| Widget | Data source | Update interval |
|---|---|---|
| Clock + date | `date` | 1s / 60s |
| Theme info | active theme + effects preset | on theme switch |
| Workspaces | `hyprctl workspaces -j` | event-driven |
| System summary | `/proc/stat`, `/proc/meminfo`, `df`, `/proc/uptime` | 5s |
| Now Playing | `playerctl` (MPRIS) | 3s, hidden when idle |

## How It Works

- `theme` generates `~/.config/eww/homepage/eww.scss` with semantic color
  variables and `eww.yuck` with the widget layout
- Helper scripts in `~/.config/eww/homepage/scripts/` poll system data
- On theme switch, `reload()` runs `eww reload` for a flicker-free color update
- Cards use the theme's `bg` at reduced opacity over the wallpaper
- Effects presets influence card opacity (minimal=0.85, cyber=0.60)

## Configuration

Stored at `~/.config/theme-engine/homepage.json`:

```json
{
  "version": 1,
  "enabled": true,
  "alignment": "left"
}
```

## Auto-Start

Add to your `hyprland.conf`:

```
exec-once = theme homepage on
```

## Enabling the Target

Add `homepage` to `~/.config/theme-engine/targets.conf` (or run `install.sh`
on a system with eww installed — it adds the line automatically).

## Troubleshooting

- **"eww not found"**: Install with `sudo pacman -S eww`
- **Overlay not showing**: Check `theme homepage` for status. Try `theme homepage restart`
- **No media widget**: Install `playerctl`. The widget auto-hides when no player is active
- **Stale process**: `theme homepage off && theme homepage on`

## Reverting

```sh
theme homepage off
rm -rf ~/.config/eww/homepage/
```

Remove `homepage` from `targets.conf` to stop regenerating.
