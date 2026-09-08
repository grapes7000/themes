# Qt Theme Studio migration

This branch begins the incremental migration of the terminal Theme Studio to the reusable PySide6/QML shell from `grapes7000/qt-app-template`.

## Routing

- `theme`, `theme studio`, and `theme edit [name]` prefer the Qt frontend.
- If PySide6 is unavailable, automatic launches retain the existing TUI fallback.
- `theme tui [name]` explicitly opens the terminal frontend.
- `theme qt [name]` explicitly requires the Qt frontend.
- `theme qt-install` creates a managed venv at `~/.local/share/theme-studio/qt-venv` and installs PySide6 there.
- Existing noninteractive commands continue through the current `theme-studio` / legacy routing unchanged.

## First Qt slice

The first UI intentionally covers a useful vertical slice rather than claiming TUI parity:

- saved-theme browser;
- core semantic role editing;
- common style editing;
- light/dark metadata;
- ThemeEditor undo/redo, recovery, dirty state, validation, save/cancel;
- live desktop preview through `theme_runtime.preview_theme`;
- Save & Apply through the saved theme path;
- self-theming from `~/.config/theme-engine/generated/theme.json`;
- validation/placeholder inspector page for the still-unmigrated advanced tools.

## Still owned by the TUI

Until migrated, keep using `theme tui` for the deeper component editors, comparison/search flows, recovery UI, advanced inspector, and theme management operations.

## Packaging

The normal installer stays lightweight. Qt/QML sources are installed to `~/.local/share/theme-studio/qt`, while PySide6 is installed only when `theme qt-install` is requested. AppImage bundling is intentionally not changed in this first pass.

## Source cleanup follow-up

`theme_schema.py`, `theme_tui.py`, and related Studio sources are still reconstructed from the split archive under `dist/`. Moving those files into normal tracked source should be a separate cleanup before the migration grows much further.
