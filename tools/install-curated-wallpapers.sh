#!/usr/bin/env bash
set -euo pipefail

src="${1:-}"
if [[ -z "$src" ]]; then
  echo "Usage: install-curated-wallpapers.sh PATH_TO_ZIP_OR_DIRECTORY" >&2
  exit 2
fi

cfg="${XDG_CONFIG_HOME:-$HOME/.config}"
dest="$cfg/hypr/wallpapers"
mkdir -p "$dest"

names=(
  monolith-dark monolith-light carbon paper terminal-green
  ibm-ish concrete ink snow obsidian-mono
)

copy_from_dir() {
  local dir="$1"
  local missing=0
  for name in "${names[@]}"; do
    if [[ -f "$dir/$name.png" ]]; then
      install -m644 "$dir/$name.png" "$dest/$name.png"
    else
      echo "Missing: $dir/$name.png" >&2
      missing=1
    fi
  done
  return "$missing"
}

if [[ -d "$src" ]]; then
  copy_from_dir "$src"
elif [[ -f "$src" ]]; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  unzip -q "$src" -d "$tmp"
  copy_from_dir "$tmp"
else
  echo "Not found: $src" >&2
  exit 1
fi

echo "Installed curated wallpapers to $dest"
echo "They are bound by filename: theme <name> switches to <name>.png automatically."
