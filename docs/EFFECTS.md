# Effects Profiles

Effects profiles control Hyprland desktop effects (blur, shadows, animations,
dimming) independently of the color theme. They override the `style` values
in a theme's JSON without modifying the file.

## Quick Start

```sh
theme effects              # show current preset (or "none")
theme effects polished     # switch to polished
theme effects --list       # list available presets
theme effects none         # clear preset, use theme defaults
```

Switching a preset re-applies the active theme immediately.

## Presets

| Preset     | Blur | Shadow | Dim   | Animations            | Notes                   |
|------------|------|--------|-------|-----------------------|-------------------------|
| `minimal`  | off  | off    | none  | disabled              | Reduced-motion friendly |
| `calm`     | light| light  | 0.05  | gentle fade+slide     | Subtle, low distraction |
| `polished` | med  | med    | 0.12  | smooth slide          | Balanced desktop feel   |
| `cyber`    | heavy| heavy  | 0.20  | fast popin+slidefade  | Maximum visual impact   |

## How It Works

- Presets are defined in `bin/theme_effects.py` as named dictionaries
- The active preset is stored in `~/.config/theme-engine/effects.json`
- When `gen_hypr()` runs, it merges the preset's style overrides on top of the
  theme's own `style` values, then appends an `animations {}` block
- Colors always come from the theme's semantic `roles` — presets never set colors

## Backward Compatibility

- If no effects profile exists (`effects.json` missing), behavior is identical
  to before: the theme's `style` values pass through unchanged and no
  `animations {}` block is generated
- Theme JSON files are never modified
- The `theme <name>` command continues to work exactly as before

## File Layout

```
~/.config/theme-engine/effects.json   # {"version": 1, "preset": "polished"}
bin/theme_effects.py                  # presets, profile load/save, animation renderer
```

## Reverting

Delete the effects profile to return to pre-effects behavior:

```sh
rm ~/.config/theme-engine/effects.json
theme <current-theme>   # re-apply to regenerate without effects
```

Or use:

```sh
theme effects none
```
