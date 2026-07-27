# Pywal feature integration plan

## Goal

Bring the useful missing capabilities from pywal into the theme engine without
turning pywal into a second application layer.

The theme engine remains the source of truth for semantic colors, visual style,
app generators, reload behavior, desktop effects, and wallpaper application.
Pywal-compatible features are added as palette input/output capabilities.

No generated palette should prefer any specific hue family. Color selection must
be based on the source image, selected preset, or explicit user overrides.

## Current overlap

The theme engine already provides several things pywal normally handles:

- named themes and reusable theme files
- 16 ANSI terminal colors
- wallpaper selection and generation
- per-application config generation
- application reloads
- light and dark themes
- predefined palettes
- desktop-wide application of a selected theme

These pieces should stay in the existing engine rather than being reimplemented
through pywal's reload and template systems.

## Missing pywal capabilities worth adopting

| Capability | Priority | Direction |
|---|---:|---|
| Standard pywal `colors.json` export | P0 | Native exporter owned by this project |
| Pywalfox live update | P0 | Run after the standard cache is written |
| Palette extraction from an image | P1 | Pluggable backend interface |
| Backend selection | P1 | `--backend` with a stable internal API |
| Dark/light palette shaping | P1 | Contrast-aware semantic-role mapper |
| Saturation adjustment | P1 | Non-destructive generation option |
| Save an extracted palette as a theme | P1 | Emit normal `themes/<name>.json` |
| Import an existing pywal theme/cache | P2 | Convert pywal fields into semantic roles |
| Palette preview | P2 | Terminal preview and machine-readable JSON |
| Cache by image/backend/options | P2 | XDG-compliant cache with versioning |
| Previous-theme history and restore | P2 | Small history file; do not copy pywal state logic |
| Directory input, recursive and iterative modes | P3 | Batch/rotation convenience feature |
| User templates | P3 | Optional generic exporter after core renderers |
| Post-apply hooks | P3 | Explicit, ordered, failure-isolated hooks |
| Partial `wal` command compatibility | P4 | Thin migration shim, not a second engine |

## Pywal features not worth copying directly

The following duplicate stronger behavior already present in the theme engine:

- pywal's wallpaper setter
- pywal's GTK, terminal, i3, Sway, and Polybar reload orchestration
- direct terminal escape-sequence broadcasting for supported native targets
- pywal-owned per-app templates for apps that already have semantic generators
- a second theme directory or second active-theme state file

Terminal escape sequences may remain an optional compatibility output later, but
should not become the primary application mechanism.

---

## Phase 0 — canonical pywal and pywalfox compatibility

### Deliverable

`bin/theme-pywalfox` exports any existing theme to:

```text
$XDG_CACHE_HOME/wal/colors.json
```

The payload contains:

- `wallpaper`
- `alpha`
- `special.background`
- `special.foreground`
- `special.cursor`
- ordered `color0` through `color15`
- optional theme-engine metadata ignored by pywal consumers

The exporter uses `$XDG_CONFIG_HOME` and `$XDG_CACHE_HOME`, writes atomically,
and can run `pywalfox update` after export.

### Why this is needed

The current inline Firefox exporter writes 16 colors but omits the required
`wallpaper` field and writes to a hard-coded `~/.cache` path. Pywalfox's native
host requires both `colors` and `wallpaper`, so the current output can be
rejected even when every color exists.

### Follow-up integration

After the standalone exporter is tested:

1. Move its reusable functions into `bin/theme_pywal.py`.
2. Add a `pywal` target to `targets.conf`.
3. Run the exporter from every normal `theme <name>` application.
4. Keep the `firefox` target responsible only for browser `userChrome.css`.
5. Run `pywalfox update` when the `pywal` target is enabled and the executable
   exists.
6. Remove the duplicate inline `colors.json` builder from `gen_firefox`.

### Acceptance criteria

- Every bundled theme produces exactly 16 ordered colors.
- Output contains a non-empty `wallpaper` string.
- Output honors XDG config and cache locations.
- Missing optional ANSI roles receive deterministic semantic fallbacks.
- Switching between two themes changes the cache and updates pywalfox.
- Export never mutates a source theme JSON file.

---

## Phase 1 — image-to-theme generation

### Proposed commands

```bash
theme from-image wallpaper.jpg --name generated-theme
theme from-image wallpaper.jpg --name generated-theme --backend colorthief
theme from-image wallpaper.jpg --name generated-theme --light
theme from-image wallpaper.jpg --name generated-theme --saturate 0.75
theme from-image wallpaper.jpg --name generated-theme --style-from polished
theme from-image wallpaper.jpg --preview
```

### Architecture

```text
image
  -> extraction backend
  -> raw color candidates
  -> palette normalizer
  -> semantic role mapper
  -> contrast validation
  -> theme.json
  -> existing app generators and reload pipeline
```

Create a small package with clear boundaries:

```text
bin/theme_palette/
  __init__.py
  model.py          # normalized palette and generation options
  color_math.py     # luminance, contrast, saturation, mixing
  extract.py        # backend registry
  map_roles.py      # raw colors -> semantic roles + ANSI colors
  cache.py          # XDG cache and versioning
  backends/
    pillow.py       # dependency-light baseline
    colorthief.py   # optional backend
    external_wal.py # temporary bridge to an installed pywal
```

### Mapping requirements

The mapper must:

- derive background and foreground using luminance rather than fixed indices
- meet readable foreground/background contrast targets
- preserve source-image character without forcing a preferred hue
- select primary and secondary accents by separation and usefulness
- generate a stable normal and bright ANSI palette
- derive `focus`, `border_normal`, `text_dim`, selection, and cursor roles
- keep style independent from extracted colors

Style should come from `--style-from`, an effects profile, or neutral defaults.
An image palette should not guess blur, gaps, shadows, or corner radius.

---

## Phase 2 — import, preview, cache, and restore

### Import

Support both standard pywal cache files and saved pywal themes:

```bash
theme import-pywal ~/.cache/wal/colors.json --name imported
theme import-pywal ~/.config/wal/colorschemes/dark/example.json --name example
```

The importer converts pywal's `special` and `color0..15` fields into the normal
semantic schema. Imported themes become ordinary project themes and require no
special runtime path.

### Preview

Add:

```bash
theme preview <name>
theme from-image image.png --preview
theme export-pywal <name> --stdout
```

Preview should show semantic roles, the ANSI palette, light/dark mode, source
wallpaper, and contrast warnings without applying the theme.

### Cache

Cache extraction results using:

- source file identity and modification time
- backend name and backend version
- dark/light mode
- saturation and adjustment options
- mapper schema version

A schema version prevents stale palettes after mapping logic changes.

### Restore

Maintain a small bounded history such as:

```text
$XDG_STATE_HOME/theme-engine/history.json
```

Commands:

```bash
theme previous
theme history
theme restore <history-index>
```

This should restore named engine themes, not pywal's separate runtime state.

---

## Phase 3 — templates, hooks, and image collections

### Generic templates

Add an optional template target only after native generators run reliably:

```text
~/.config/theme-engine/templates/*.in
```

Template variables should expose both semantic roles and pywal-compatible names.
Native generators remain preferred because they can handle app-specific merging,
backup, reload, and validation.

### Hooks

Add ordered hooks:

```text
~/.config/theme-engine/hooks/post-apply.d/
```

Requirements:

- execute in lexical order
- receive theme name and generated artifact paths through environment variables
- isolate failures so one hook cannot corrupt the apply process
- report failures clearly
- support a strict mode for automation and tests

### Image collections

Later commands may support directories:

```bash
theme from-image ~/Wallpapers --random
theme from-image ~/Wallpapers --recursive
theme from-image ~/Wallpapers --iterative
theme rotate next
```

Generated themes should reference their source image and generation options so
they remain reproducible.

---

## Phase 4 — optional `wal` migration shim

Provide only the subset useful for existing scripts:

```bash
wal -i image.png
wal -R
wal --theme name
wal --preview
```

The shim should translate arguments into `theme` commands. It must not maintain
another cache, theme directory, reload pipeline, or source of truth.

---

## Testing strategy

### Unit tests

- semantic fallback to all 16 ANSI slots
- pywal JSON schema and ordering
- XDG path handling
- atomic cache replacement
- luminance and contrast calculations
- deterministic palette generation
- import/export round trips
- malformed image and malformed theme handling

### Fixture tests

Include representative fixtures for:

- dark photograph
- light photograph
- low-saturation image
- high-saturation image
- nearly monochrome image
- image with one dominant color
- transparent PNG
- incomplete but valid semantic theme

### Integration tests

- export every bundled theme and validate pywalfox input
- apply two themes and confirm cache changes
- run with a temporary HOME, XDG_CONFIG_HOME, and XDG_CACHE_HOME
- run without pywalfox installed
- run with a fake `pywalfox` executable and confirm `update` is called
- verify source themes and user configs are unchanged

## Recommended implementation order

1. Land and test the standalone pywalfox exporter.
2. Integrate it as the always-available `pywal` target.
3. Add an external-pywal extraction bridge for fast validation.
4. Implement the internal extraction backend interface.
5. Add semantic mapping and contrast validation.
6. Add save, preview, import, cache, and restore.
7. Add templates, hooks, directory input, and the optional `wal` shim.

This sequence gives immediate compatibility first, then adds image-derived themes
without destabilizing the existing desktop application pipeline.
