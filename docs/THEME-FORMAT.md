# The `theme.json` format

Every theme is a single JSON file in `themes/<name>.json` with four top-level
keys: `name`, `dark`, `roles`, `style`.

```jsonc
{
  "name": "catppuccin_mocha",
  "dark": true,
  "roles":  { /* colors  */ },
  "style":  { /* feel    */ }
}
```

---

## `roles` — semantic colors

All values are `#RRGGBB` hex strings.

| Key | Used for |
|---|---|
| `bg` | Window/root background, base surface |
| `bg_alt` | Bar background, secondary surface |
| `text` | Primary text/foreground |
| `text_dim` | Secondary/muted text |
| `focus` | **Focused** window border, active accents |
| `border_normal` | Unfocused window border |
| `accent` | Primary accent (highlights, prompt) |
| `accent2` | Secondary accent (gradients, second color) |
| `urgent` | Urgent windows / error states |
| `sel_bg`, `sel_fg` | Terminal selection colors |
| `cursor` | Terminal cursor |
| `ansi_black … ansi_white` | The 8 normal ANSI terminal colors |
| `ansi_br_black … ansi_br_white` | The 8 bright ANSI terminal colors |

Minimum you must set for a good result: `bg`, `bg_alt`, `text`, `text_dim`,
`focus`, `border_normal`, `accent`, `accent2`, `urgent`. The ANSI set drives
kitty's palette.

---

## `style` — the feel

| Key | Type | Meaning |
|---|---|---|
| `corner_radius` | int px | Window/rounding. `0` = sharp (see y2k, vintage-mac) |
| `opacity` | 0–1 | Focused window opacity |
| `opacity_inactive` | 0–1 | Unfocused window opacity |
| `inactive_dim` | 0–1 | Dim strength on unfocused windows (`0` = off) |
| `blur_on` | `"true"`/`"false"` | Enable background blur |
| `blur_strength` | int | Blur size (higher = softer/heavier) |
| `shadow_on` | `"true"`/`"false"` | Enable drop shadows |
| `shadow_radius` | int px | Shadow spread |
| `shadow_opacity` | 0–1 | Shadow darkness |
| `shadow_offset` | int px | Shadow vertical offset (negative = up) |
| `shadow_color` | `#RRGGBB` | Shadow tint (defaults to black) |
| `gaps` | int px | Gap between tiles; `gaps_in` is derived as `gaps/2` |
| `border_width` | int px | Window border thickness |
| `font`, `fontsize`, `term_fontsize` | | Fonts |
| `bar_height`, `bar_margin` | | Reserved for bar styling |

### Design guidance (make the feel fit the palette)

- **Glassy / soft** (catppuccin, tokyonight, ios-glassy): big `corner_radius`
  (12–16), high `blur_strength` (9–12), lower `opacity` (0.92–0.95), generous
  `gaps` (9–12), soft shadows.
- **Sharp / retro** (y2k, vintage-mac, monokai): `corner_radius` 0–4,
  `blur_on:false` (or very low), tight `gaps` (4–6), thicker `border_width`,
  hard shadows.
- **Light themes**: keep shadows subtle (`shadow_opacity` 0.08–0.15) — heavy
  shadows look muddy on light backgrounds. Lower `blur_strength` (4–6).
- **Neon / mono** (cyber-green, hacker-pink): tint `shadow_color` with the
  accent for a glow.

---

## What gets generated

Running `theme <name>` writes (never edit these by hand):

- `~/.config/hypr/generated/theme.conf` — `general{}` border colors + gaps,
  `decoration{}` rounding/opacity/blur/shadow, and `$color` variables.
- `~/.config/waybar/generated/theme.css` — `@define-color` for each role.
- `~/.config/kitty/generated/theme.conf` — `background`/`foreground` + the 16
  `color0..15` ANSI entries + `font_size`.
- `~/.config/starship.toml` — a `[palettes.theme]` block + prompt styling.
- `~/.oh-my-zsh/custom/themes/theme-engine.zsh-theme` — an oh-my-zsh prompt
  theme (only if oh-my-zsh is installed; `ZSH_THEME` is set to it once).
- `~/.config/nvim/lua/generated_theme.lua` — a full Neovim colorscheme (base
  highlight groups + treesitter `@capture` links) built from the palette.
- `~/.config/hypr/wallpapers/<name>.png` — via `wallgen`.

The active theme name is recorded in
`~/.config/hypr/generated/.active`.

---

## Adding a new target app

`bin/theme` is small Python. To theme another app, add a `gen_<app>(roles,
style)` that writes its config from the roles/style, and call it from
`apply()`. The pattern is: read `roles`/`style`, format the app's config
syntax, `write()` it, then reload the app in `reload()`.
