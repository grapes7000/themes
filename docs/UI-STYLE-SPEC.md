# Semantic UI Style Profiles

UI style profiles are the application-layout counterpart to color themes.

A color theme answers **what colors mean**. A UI style profile answers **how the interface is built**.

The two axes are intentionally independent:

```text
color theme                         UI style
-----------                         --------
background / surface roles          spacing rhythm
text / muted text                   control heights
accent / selection                  corner radii
success / warning / danger          border widths
semantic status colors              typography scale
                                    icon geometry
                                    section/list/dialog patterns
```

This lets the same `graphite`, `y2k`, or `catppuccin` palette be rendered as a crisp precision desktop app, a roomy legacy app, or a retro Win95-style app without changing the application's business logic.

## Commands

```bash
theme ui                 # show resolved style
theme ui --list          # list profiles
theme ui precision       # force Precision for every theme
theme ui legacy          # force the previous roomy/rounded grammar
theme ui win95           # force retro Win95 grammar
theme ui auto            # follow the selected theme's ui_style, else Precision
```

The selected profile is published atomically to:

```text
~/.config/theme-engine/generated/ui-style.json
```

Application consumers should watch this file the same way they watch the color contract.

## Linking a style to a theme

A theme may optionally declare a default UI style:

```json
{
  "name": "graphite",
  "ui_style": "precision",
  "roles": { ... },
  "style": { ... }
}
```

This link is only used while `theme ui auto` is active. An explicit `theme ui <name>` override always wins.

Resolution order:

1. explicit user override (`theme ui precision`)
2. current theme's `ui_style`
3. `precision`

This means themes can ship a recommended visual grammar without taking control away from the user.

## Schema version 1

Each file under `ui-styles/*.json` contains:

```jsonc
{
  "schema_version": 1,
  "name": "precision",
  "description": "...",
  "metrics": { ... },
  "patterns": { ... },
  "rules": { ... }
}
```

### Metrics

Metrics are semantic design tokens. Pages should not invent alternate values locally.

Required tokens:

| Token | Meaning |
|---|---|
| `grid` | base layout unit |
| `spacing_xs..spacing_3xl` | approved spacing ladder |
| `page_padding` | normal page edge inset |
| `page_padding_compact` | compact-window inset |
| `section_gap` | vertical gap between major sections |
| `control_height_compact` | icon/micro control height |
| `control_height` | normal control height |
| `control_height_large` | rare prominent control height |
| `sidebar_width` | standard navigation rail width |
| `icon_size` | normal glyph size |
| `icon_box` | optical icon alignment box |
| `radius_control` | buttons/fields/nav selections |
| `radius_surface` | ordinary raised/selected surfaces |
| `radius_overlay` | dialogs/popovers |
| `border_width` | structural/control border width |
| `focus_width` | keyboard focus line width |
| `font_caption` | smallest metadata |
| `font_secondary` | secondary UI copy |
| `font_body` | normal UI text |
| `font_section` | section label |
| `font_title` | page title |

### Patterns

Patterns describe component *behavior and composition*, not colors. Consumers map these values to their own reusable components.

| Token | Example values | Meaning |
|---|---|---|
| `surface` | `flat`, `card`, `bevel` | ordinary surface treatment |
| `section` | `divider`, `card`, `group` | how sections establish hierarchy |
| `list_row` | `flat`, `card` | data row construction |
| `selection` | `accent-soft-marker`, `filled`, `solid-accent` | selected-item presentation |
| `button` | `quiet`, `filled`, `bevel` | normal button construction |
| `field` | `outlined`, `filled-outlined`, `sunken` | text/input treatment |
| `dialog` | `elevated`, `rounded-card`, `framed` | overlay/dialog treatment |
| `status` | `semantic-muted`, `semantic-direct` | status color intensity |
| `shadow` | `overlay-only`, `soft`, `hard` | where/how depth may appear |

These names are deliberately semantic. A QML page should ask for a `button` or `section`, never ask whether it should draw a particular one-off radius or color.

### Rules

Rules are machine-readable design-discipline declarations. They exist so a future linter can catch visual drift.

`precision` is intentionally strict:

```json
{
  "allow_local_spacing": false,
  "allow_local_radius": false,
  "allow_local_font_size": false,
  "allow_local_border_width": false,
  "allow_nested_cards": false
}
```

## Precision profile

`precision` is the default professional desktop grammar.

Core rules:

- 4px base grid.
- Almost all spacing must come from 4/8/12/16/20/24/32.
- Normal controls are 30px tall.
- Ordinary radii are 3-4px; overlays cap at 8px.
- Borders and focus lines are 1px.
- Page titles are 16px, body text 13px.
- Structural hierarchy comes from alignment, spacing, and hairline dividers rather than nested cards.
- Hover is a subtle semantic surface shift.
- Selection is a muted accent surface plus a small accent marker.
- Semantic colors are reserved for actual state: success, warning, danger, information.
- Shadows are for overlays, not ordinary content sections.

### Canonical page rhythm

```text
page edge
  20px
page title (16 semibold)
  4px
subtitle (11-12 muted)
  16px
section label (13 semibold)
  8px
content rows (30px controls / compact flat rows)
  20px
1px divider when structural separation is needed
  20px
next section
```

Optical correction is permitted inside shared components, but pages may not invent new spacing tokens to make one screen "look right".

## Legacy profile

`legacy` preserves the earlier roomy Qt aesthetic for comparison and regression testing. It intentionally allows larger cards, larger radii, taller controls and more local freedom. It is not the default quality target.

## Win95 profile

`win95` provides the first deliberately different visual grammar. It uses square geometry, compact controls and semantic patterns such as `bevel`, `sunken`, and `framed`.

The palette still comes from the active theme. A Win95-style app can therefore be pink/black, graphite, Catppuccin, or any future palette without putting literal colors into its components.

## Consumer contract

Application code should have one style adapter/singleton that consumes `ui-style.json` and exposes semantic tokens. Pages and feature components then depend only on that adapter.

Good:

```qml
height: UiStyle.controlHeight
radius: UiStyle.radiusControl
spacing: UiStyle.spacingSm
```

Bad:

```qml
height: 34
radius: 7
spacing: 10
```

Even better is to centralize common patterns into reusable components (`UiButton`, `UiField`, `UiSection`, `UiListRow`, `UiDialog`) so page code rarely mentions geometry at all.

## Professional consistency checklist

A conforming Precision screen should satisfy all of these:

- no hard-coded radii in page files
- no hard-coded font sizes in page files
- no arbitrary spacing values outside shared components
- no border wider than the profile token
- no nested decorative cards
- no status color used purely for selection/decorative emphasis
- no unique button height for one page
- icons use the standard optical box
- labels/controls share deliberate alignment axes
- data rows use one canonical row pattern
- dialog actions use the same control primitive as page actions
- color comes only from semantic theme roles

If a page genuinely needs a new visual concept, add a semantic token or shared component to the system first instead of styling that page locally.
