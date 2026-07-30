#!/usr/bin/env bash
# Build a self-contained Theme Engine AppDir/AppImage.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="$ROOT/dist"
APPDIR_ONLY=0

usage() {
    echo "Usage: packaging/build-appimage.sh [--appdir-only] [--output DIR]"
    echo "Builds dist/Theme_Engine-<arch>.AppImage, or an AppDir for inspection."
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --appdir-only) APPDIR_ONLY=1 ;;
        --output)
            [ "$#" -gt 1 ] || { echo "--output needs a directory" >&2; exit 2; }
            OUTPUT="$2"; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

command -v python3 >/dev/null || { echo "python3 is required to build" >&2; exit 1; }
mkdir -p "$OUTPUT"
APPDIR="$OUTPUT/ThemeEngine.AppDir"
[ ! -e "$APPDIR" ] || {
    echo "$APPDIR already exists; move or remove it before rebuilding." >&2
    exit 1
}

mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib/theme-engine" \
         "$APPDIR/usr/share/theme-engine/themes" "$APPDIR/usr/share/theme-engine/wallpapers" \
         "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/scalable/apps"

install -m755 "$(command -v python3)" "$APPDIR/usr/bin/python3"
PY_STDLIB="$(python3 -c 'import sysconfig; print(sysconfig.get_path("stdlib"))')"
PY_VERSION="$(python3 -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}")')"
cp -a "$PY_STDLIB" "$APPDIR/usr/lib/$PY_VERSION"

copy_dependencies() {
    local binary="$1" lib
    while IFS= read -r lib; do
        [ -f "$lib" ] || continue
        [ -e "$APPDIR/usr/lib/$(basename "$lib")" ] || cp -L "$lib" "$APPDIR/usr/lib/"
    done < <(ldd "$binary" 2>/dev/null | awk '/=> \// {print $3} /^\// {print $1}')
}
copy_dependencies "$(command -v python3)"
while IFS= read -r -d '' extension; do
    copy_dependencies "$extension"
done < <(find "$APPDIR/usr/lib/$PY_VERSION" -type f -name '*.so' -print0)

for file in theme theme-new theme-menu wallgen starship-config \
            theme-pywalfox theme-stylus theme-from-image \
            theme_starship.py theme_effects.py theme_homepage.py; do
    install -m755 "$ROOT/bin/$file" "$APPDIR/usr/lib/theme-engine/$file"
done
cp "$ROOT"/themes/*.json "$APPDIR/usr/share/theme-engine/themes/"
cp "$ROOT"/wallpapers/*.png "$APPDIR/usr/share/theme-engine/wallpapers/" 2>/dev/null || true

install -m755 "$ROOT/packaging/AppRun" "$APPDIR/AppRun"
install -m644 "$ROOT/packaging/theme-engine.desktop" "$APPDIR/theme-engine.desktop"
install -m644 "$ROOT/packaging/theme-engine.desktop" "$APPDIR/usr/share/applications/theme-engine.desktop"
install -m644 "$ROOT/packaging/theme-engine.svg" "$APPDIR/theme-engine.svg"
install -m644 "$ROOT/packaging/theme-engine.svg" \
    "$APPDIR/usr/share/icons/hicolor/scalable/apps/theme-engine.svg"
ln -s theme-engine.svg "$APPDIR/.DirIcon"

if [ "$APPDIR_ONLY" -eq 1 ]; then
    echo "AppDir ready: $APPDIR"
    exit 0
fi

command -v appimagetool >/dev/null || {
    echo "AppDir ready: $APPDIR" >&2
    echo "Install appimagetool, then rerun this command to produce the AppImage." >&2
    exit 1
}
ARCH="${ARCH:-$(uname -m)}"
case "$ARCH" in
    x86_64|amd64) ARCH=x86_64 ;;
    aarch64|arm64) ARCH=aarch64 ;;
esac
DEST="$OUTPUT/Theme_Engine-$ARCH.AppImage"
ARCH="$ARCH" appimagetool "$APPDIR" "$DEST"
echo "AppImage ready: $DEST"
