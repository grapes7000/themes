# Theme Role Contract

All UI elements use roles from this contract. Theme JSONs define the **core** roles; the engine derives the **semantic** roles automatically from them. A theme may explicitly set any semantic role to override the default.

## Core roles (required in every theme JSON)

| Role            | Purpose                      |
|-----------------|------------------------------|
| `bg`            | Primary background           |
| `bg_alt`        | Secondary/bar background     |
| `text`          | Primary foreground           |
| `text_dim`      | Muted/secondary text         |
| `accent`        | Primary accent               |
| `accent2`       | Secondary accent             |
| `urgent`        | Error/urgent state           |
| `focus`         | Focused window border        |
| `border_normal` | Unfocused window border      |

## Semantic roles (auto-derived, overridable)

| Role            | Default derivation                            |
|-----------------|-----------------------------------------------|
| `surface_0`     | `bg`                                          |
| `surface_1`     | `bg_alt`                                      |
| `surface_2`     | blend(`bg_alt`, `text`, 8%)                   |
| `overlay`       | `bg`                                          |
| `hover`         | blend(`bg_alt`, `accent`, 15%)                |
| `selected`      | `accent`                                      |
| `border_subtle` | `border_normal`                               |
| `border_strong` | `focus`                                       |
| `success`       | `ansi_green` or `accent2`                     |
| `warning`       | `ansi_yellow` or `accent2`                    |
| `info`          | `ansi_blue` or `accent2`                      |
| `disabled`      | `text_dim`                                    |
| `shadow`        | style `shadow_color` or `#000000`             |
| `on_accent`     | whichever of `bg`/`text` contrasts `accent`   |
| `on_urgent`     | whichever of `bg`/`text` contrasts `urgent`   |

## Generator usage

- **Waybar** (`theme.css`): all core + semantic roles as `@define-color`
- **Hyprland** (`theme.conf`): core vars + `$group_active`, `$group_inactive`, `$group_locked`, `$group_text`
- **Dunst** (`dunstrc`): urgency levels use `info`/`accent`/`urgent` frame colors
- **Wofi** (`colors.css`): adds `hover`, `selected`, `disabled`, `on_accent`
- **Rofi** (`theme-engine.rasi`): adds `hover`, `selected`, `on_accent`

## Backward compatibility

Existing theme JSONs require no changes. All semantic roles fall back to core roles when not explicitly defined. The `resolve_semantic_roles()` function is pure and deterministic.
