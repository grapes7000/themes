# Stylus webpage theming

`theme-stylus` converts any installed theme-engine theme into a Stylus-compatible
UserCSS file for normal web pages. It complements Pywalfox:

- Pywalfox themes Firefox and Thunderbird chrome.
- Stylus injects CSS into web content.

The exporter never edits a source theme and does not touch the Stylus extension
database directly.

## Install Stylus

Install the official Stylus extension in Firefox. Stylus is the userstyle manager
from `openstyles/stylus`, not the similarly named CSS preprocessor.

## Generate and install the safe profile

```bash
theme-stylus catppuccin_mocha --open
```

The command writes:

```text
$XDG_CONFIG_HOME/theme-engine/stylus/theme-engine-soft.user.css
```

Firefox opens the generated file. Confirm the installation in Stylus.

The soft profile intentionally changes only:

- browser-native light/dark color scheme
- selection colors
- scrollbars
- form-control accent color and carets
- keyboard focus rings

It avoids replacing website surfaces, layouts, images, video, or SVG.

## Optional full recolor

```bash
theme-stylus catppuccin_mocha --profile full --open
```

The full profile additionally recolors common page surfaces, text, links, form
controls, code blocks, and borders. It is more visually complete but can conflict
with complex sites. Disable the style from the Stylus toolbar on any site that
looks wrong.

## Use the active theme

After applying a desktop theme, omit the name:

```bash
theme catppuccin_mocha
theme-stylus --open
```

## Regenerate after a theme change

```bash
theme-stylus nord
```

This updates the generated file atomically. The first version does not modify
Stylus storage automatically, so refresh or reinstall the generated UserCSS in
Stylus after regeneration. Automatic local live reload belongs in a later,
browser-specific integration because direct IndexedDB modification would be
fragile and unsafe.

## Other commands

```bash
# Print without writing
theme-stylus nord --stdout

# Write somewhere else
theme-stylus nord --output /tmp/nord.user.css

# Stronger global profile
theme-stylus nord --profile full
```

## Safety choices

The generated style:

- applies only to `http://` and `https://` pages
- does not style Firefox internal pages or extension pages
- does not alter geometry, spacing, positioning, images, video, or SVG
- keeps the full profile optional
- uses prefixed CSS variables to reduce collisions with site variables
