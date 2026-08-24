# Theme target presets

The theme engine is standalone and does not install distro packages or shell frameworks. `targets.conf` decides which generators are active on a machine.

## Install modes

```bash
./install.sh --targets auto
./install.sh --targets terminal
./install.sh --targets full
```

`auto` is the default. It detects the desktop and enables usable generators.

`terminal` is intended for WSL, servers, minimal Ubuntu/Arch installs, and homelab machines. It considers only Kitty, Starship, Neovim, and Zsh targets. Missing programs remain commented out rather than being installed by this repository.

`full` writes the complete Hyprland-oriented target set for a machine that already has the required desktop software.

The installer never overwrites an existing `~/.config/theme-engine/targets.conf`, so target changes remain explicit.

## Ownership

- package installation and machine profiles: `linux-setup`
- application behavior/configuration: `dotfiles`
- generated colors/theme assets: this repository
- Arch/Hyprland/Quickshell session integration: `Arch-WM-install`

Generated Neovim colors belong here. Neovim plugins, mappings, LSP/editor behavior, and learning-friendly Vim configuration belong in `dotfiles`.
