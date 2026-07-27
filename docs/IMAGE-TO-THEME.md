# Image-to-theme generation with pywal16

`theme-from-image` turns an image into a normal reusable theme-engine theme.
Pywal16 is used only for palette extraction. The command explicitly disables
Pywal's wallpaper setter, terminal escape sequences, TTY updates, and desktop
reload hooks, so the existing theme engine remains the only application layer.

## Install pywal16 on Arch

```bash
sudo pacman -S --needed imagemagick python-pipx
pipx install "pywal16[all]"
```

Open a new shell and verify:

```bash
wal -v
wal --backend
```

The command requires the maintained pywal16 fork. It rejects the archived
original Pywal because image themes depend on its 16-color and isolated output
features.

## Create and apply a dark theme

```bash
theme-from-image ~/Pictures/sunset.jpg --name sunset --apply
```

This creates:

```text
~/.config/hypr/themes/sunset.json
~/.config/hypr/wallpapers/sunset.png
```

The generated theme inherits visual settings such as rounding, gaps, opacity,
blur, and shadows from the currently active theme. Only the palette changes.
Use `--style-from <theme>` to choose a different source explicitly.

## Preview without writing

```bash
theme-from-image ~/Pictures/sunset.jpg --name sunset --preview
```

## Light theme

```bash
theme-from-image ~/Pictures/daylight.jpg --name daylight --light --apply
```

## Palette controls

```bash
# Pick a pywal16 backend
theme-from-image image.jpg --name image-theme --backend colorthief --apply

# Adjust saturation
theme-from-image image.jpg --name vivid --saturate 0.35 --apply

# Request a minimum contrast ratio
theme-from-image image.jpg --name readable --contrast 3.0 --apply

# Choose the 16-color shaping method
theme-from-image image.jpg --name dual --cols16 dual --apply
```

Available `--cols16` values are `darken`, `lighten`, `dual`,
`foxify-darken`, `foxify-lighten`, and `foxify-dual`.

## Replacing a generated theme

The command refuses to overwrite an existing theme or wallpaper by default.
Regenerate intentionally with:

```bash
theme-from-image image.jpg --name sunset --force --apply
```

## Mapping behavior

The exporter preserves Pywal's complete `color0` through `color15` palette.
Semantic background, foreground, and cursor roles come from Pywal's `special`
object. Primary and secondary accents are selected deterministically from the
palette using contrast, saturation, and color separation rather than preferring
a particular hue family.

Generated files include metadata recording the backend, 16-color method,
saturation, contrast, and inherited style source. Source images and source theme
files are never modified.
