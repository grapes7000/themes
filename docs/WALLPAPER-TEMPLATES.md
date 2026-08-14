# Semantic wallpaper templates

Theme Engine can recolor one flat-color artwork across every theme by mapping the artwork's source colors to semantic theme roles.

A template answers one question once: **what does each color region mean?** After that, `theme nord`, `theme gruvbox`, a generated pywal theme, or any future theme uses its own values for those roles automatically.

## Built-in Arch retro template

The repository ships the Arch retro stripe wallpaper as `wallpapers/arch-retro-source.png`. The six regions are mapped as:

| Source color | Semantic role |
|---|---|
| `#282828` | `bg` |
| `#ebdbb2` | `text` |
| `#689d6a` | `ansi_green` |
| `#458588` | `ansi_blue` |
| `#d79921` | `ansi_yellow` |
| `#cc241d` | `ansi_red` |

Activate it with:

```bash
theme wallpaper use arch-retro
```

Then switch normally:

```bash
theme gruvbox
theme nord
```

The same artwork is regenerated with the selected theme's palette and set through hyprpaper.

Disable semantic recoloring without deleting normal wallpapers:

```bash
theme wallpaper none
```

## Import any flat-color image

For a normal image:

```bash
theme wallpaper import ~/Pictures/wallpaper.png --name my-wallpaper
```

The importer detects dominant flat colors, filters tiny anti-aliased fringe colors, suggests a semantic role for each region, and asks you to confirm or replace each suggestion. Press **Enter** to accept a suggestion.

Example interaction:

```text
Detected 6 dominant regions in wallpaper.png:
  #282828   90.83%  semantic role [bg]:
  #689d6a    2.05%  semantic role [ansi_green]:
  #458588    2.02%  semantic role [ansi_blue]:
  #d79921    1.99%  semantic role [ansi_yellow]:
  #cc241d    1.96%  semantic role [ansi_red]:
  #ebdbb2    0.59%  semantic role [text]:
```

If the artwork was designed for an existing theme, pass it as a reference. Exact source-color matches are recognized before hue-based suggestions:

```bash
theme wallpaper import ~/Pictures/wallpaper.png --name my-wallpaper --palette gruvbox
```

For automation or a known-good flat palette, accept all suggestions without prompts:

```bash
theme wallpaper import ~/Pictures/wallpaper.png --name my-wallpaper --yes
```

Import without activating it:

```bash
theme wallpaper import ~/Pictures/wallpaper.png --name my-wallpaper --no-use
```

## Manage templates

```bash
theme wallpaper
theme wallpaper --list
theme wallpaper use my-wallpaper
theme wallpaper none
```

User templates are stored at:

```text
~/.config/theme-engine/wallpaper-templates/<name>/
├── source.png
└── template.json
```

Rendered files are cache artifacts, not replacements for your existing wallpapers:

```text
~/.cache/theme-engine/wallpapers/<template>/<theme>.png
```

This keeps `wallgen`'s normal `~/.config/hypr/wallpapers/<theme>.png` files untouched. Turning semantic wallpapers off therefore falls back cleanly to the existing wallpaper system.

## How edge preservation works

The renderer does more than exact color replacement. Flat fills map directly to their target roles. For non-palette pixels near an edge, it finds the best blend between two source-region colors and recreates that same blend using the two target theme colors. This keeps anti-aliased curves and diagonals from retaining a thin fringe of the original theme.

Pixels that do not look like a plausible blend between mapped regions are left unchanged instead of being force-recolored. That makes small unrelated details safer.

## What images work best?

Best results come from artwork with a limited, intentional palette: vector-style wallpapers, pixel art, logos, geometric graphics, Y2K/retro graphics, and illustrations with large flat regions.

Gradients and shaded art can work partially, but this first version is intentionally conservative. Photographs are not good automatic-template candidates because similar pixel colors can belong to unrelated objects. A future mask mode can let Krita-defined regions separate those cases explicitly.

## Direct `wallgen` interface

`theme wallpaper ...` is the user-facing command. The lower-level equivalent is available for debugging:

```bash
wallgen semantic
wallgen semantic list
wallgen semantic use arch-retro
wallgen semantic import IMAGE --name NAME
wallgen semantic apply nord --set
```

The original blurry generator remains backward compatible:

```bash
wallgen
wallgen nord
wallgen nord --set
```
