#!/usr/bin/env python3
"""Safe working-copy lifecycle for Theme Studio."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any, Callable

from theme_schema import dump_json, ensure_theme_schema, safe_theme_name, synchronize_style, validate_theme


class EditorError(RuntimeError):
    pass


def _default_theme_dir() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "hypr" / "themes"


def _state_dir() -> Path:
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "theme-studio"


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent), text=True)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


@dataclass
class Snapshot:
    label: str
    data: dict[str, Any]
    created_at: float = field(default_factory=time.time)


@dataclass
class ThemeEditor:
    theme_name: str
    theme_dir: Path = field(default_factory=_default_theme_dir)
    preview_callback: Callable[[dict[str, Any], str], None] | None = None
    restore_callback: Callable[[str], None] | None = None
    max_history: int = 100

    original: dict[str, Any] = field(init=False)
    draft: dict[str, Any] = field(init=False)
    undo_stack: list[Snapshot] = field(default_factory=list, init=False)
    redo_stack: list[Snapshot] = field(default_factory=list, init=False)
    dirty: bool = field(default=False, init=False)
    desktop_preview: bool = field(default=False, init=False)
    last_saved_path: Path | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.theme_dir = Path(self.theme_dir).expanduser()
        path = self.theme_path(self.theme_name)
        if not path.exists():
            raise EditorError(f"Theme not found: {self.theme_name}")
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EditorError(f"Could not read {path}: {exc}") from exc
        self.original = ensure_theme_schema(loaded)
        self.draft = deepcopy(self.original)

    @classmethod
    def from_data(cls, name: str, data: dict[str, Any], theme_dir: Path | None = None,
                  preview_callback: Callable[[dict[str, Any], str], None] | None = None,
                  restore_callback: Callable[[str], None] | None = None) -> "ThemeEditor":
        obj = cls.__new__(cls)
        obj.theme_name = safe_theme_name(name)
        obj.theme_dir = Path(theme_dir or _default_theme_dir()).expanduser()
        obj.preview_callback = preview_callback
        obj.restore_callback = restore_callback
        obj.max_history = 100
        obj.original = ensure_theme_schema(data)
        obj.draft = deepcopy(obj.original)
        obj.undo_stack = []
        obj.redo_stack = []
        obj.dirty = False
        obj.desktop_preview = False
        obj.last_saved_path = None
        return obj

    @property
    def recovery_path(self) -> Path:
        return _state_dir() / "recovery" / f"{safe_theme_name(self.theme_name)}.json"

    def theme_path(self, name: str | None = None) -> Path:
        return self.theme_dir / f"{safe_theme_name(name or self.theme_name)}.json"

    def snapshot(self, label: str) -> None:
        self.undo_stack.append(Snapshot(label, deepcopy(self.draft)))
        if len(self.undo_stack) > self.max_history:
            del self.undo_stack[: len(self.undo_stack) - self.max_history]
        self.redo_stack.clear()

    def mutate(self, label: str, mutator: Callable[[dict[str, Any]], None], preview: bool = True) -> None:
        before = deepcopy(self.draft)
        mutator(self.draft)
        synchronize_style(self.draft)
        if self.draft == before:
            return
        self.undo_stack.append(Snapshot(label, before))
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.dirty = self.draft != self.original
        self._write_recovery()
        if preview and self.desktop_preview:
            self.preview(label)

    def replace_draft(self, label: str, data: dict[str, Any], preview: bool = True) -> None:
        before = deepcopy(self.draft)
        candidate = ensure_theme_schema(data)
        if candidate == before:
            return
        self.undo_stack.append(Snapshot(label, before))
        self.redo_stack.clear()
        self.draft = candidate
        self.dirty = self.draft != self.original
        self._write_recovery()
        if preview and self.desktop_preview:
            self.preview(label)

    def undo(self) -> str | None:
        if not self.undo_stack:
            return None
        snap = self.undo_stack.pop()
        self.redo_stack.append(Snapshot(snap.label, deepcopy(self.draft)))
        self.draft = deepcopy(snap.data)
        self.dirty = self.draft != self.original
        self._write_recovery()
        if self.desktop_preview:
            self.preview(f"Undo {snap.label}")
        return snap.label

    def redo(self) -> str | None:
        if not self.redo_stack:
            return None
        snap = self.redo_stack.pop()
        self.undo_stack.append(Snapshot(snap.label, deepcopy(self.draft)))
        self.draft = deepcopy(snap.data)
        self.dirty = self.draft != self.original
        self._write_recovery()
        if self.desktop_preview:
            self.preview(f"Redo {snap.label}")
        return snap.label

    def reset_section(self, path: str) -> None:
        from theme_schema import deep_get, deep_set
        original = deepcopy(deep_get(self.original, path))
        self.mutate(f"Reset {path}", lambda d: deep_set(d, path, original))

    def reset_all(self) -> None:
        self.replace_draft("Reset theme", self.original)

    def preview(self, reason: str = "Preview") -> None:
        if self.preview_callback:
            self.preview_callback(deepcopy(self.draft), reason)

    def set_desktop_preview(self, enabled: bool) -> None:
        self.desktop_preview = bool(enabled)
        if enabled:
            self.preview("Enable live preview")
        elif self.restore_callback:
            self.restore_callback(self.theme_name)

    def validate(self) -> list[dict[str, str]]:
        return validate_theme(self.draft)

    def save(self, name: str | None = None, replace: bool = False, apply: bool = True) -> Path:
        target_name = safe_theme_name(name or self.theme_name)
        target = self.theme_path(target_name)
        if target.exists() and target_name != self.theme_name and not replace:
            raise EditorError(f"Theme already exists: {target_name}")
        errors = [issue for issue in self.validate() if issue["level"] == "error"]
        if errors:
            raise EditorError(f"Theme has {len(errors)} validation error(s); fix them before saving.")
        synchronize_style(self.draft)
        self.draft["version"] = max(3, int(self.draft.get("version", 3)))
        self.draft.setdefault("studio", {})["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        if target.exists():
            backup_dir = _state_dir() / "backups" / target_name
            backup_dir.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y%m%d-%H%M%S")
            shutil.copy2(target, backup_dir / f"{stamp}.json")
        _atomic_write(target, dump_json(self.draft))
        self.theme_name = target_name
        self.original = deepcopy(self.draft)
        self.dirty = False
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.last_saved_path = target
        self.recovery_path.unlink(missing_ok=True)
        if apply and self.preview_callback:
            self.preview_callback(deepcopy(self.draft), "Save & Apply")
        return target

    def cancel(self) -> None:
        if self.desktop_preview and self.restore_callback:
            self.restore_callback(self.theme_name)
        self.draft = deepcopy(self.original)
        self.dirty = False
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.recovery_path.unlink(missing_ok=True)

    def _write_recovery(self) -> None:
        path = self.recovery_path
        payload = {
            "theme_name": self.theme_name,
            "saved_at": time.time(),
            "original": self.original,
            "draft": self.draft,
        }
        try:
            _atomic_write(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        except OSError:
            pass

    @staticmethod
    def recoveries() -> list[dict[str, Any]]:
        directory = _state_dir() / "recovery"
        if not directory.exists():
            return []
        result = []
        for path in sorted(directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                data["path"] = str(path)
                result.append(data)
            except (OSError, json.JSONDecodeError):
                continue
        return result

    @classmethod
    def from_recovery(cls, recovery: dict[str, Any], theme_dir: Path | None = None,
                      preview_callback: Callable[[dict[str, Any], str], None] | None = None,
                      restore_callback: Callable[[str], None] | None = None) -> "ThemeEditor":
        obj = cls.from_data(recovery["theme_name"], recovery["original"], theme_dir,
                            preview_callback, restore_callback)
        obj.draft = ensure_theme_schema(recovery["draft"])
        obj.dirty = obj.draft != obj.original
        obj._write_recovery()
        return obj


def list_themes(theme_dir: Path | None = None) -> list[str]:
    directory = Path(theme_dir or _default_theme_dir()).expanduser()
    return sorted(path.stem for path in directory.glob("*.json") if path.is_file())


def load_theme(name: str, theme_dir: Path | None = None) -> dict[str, Any]:
    directory = Path(theme_dir or _default_theme_dir()).expanduser()
    path = directory / f"{safe_theme_name(name)}.json"
    return ensure_theme_schema(json.loads(path.read_text(encoding="utf-8")))


def duplicate_theme(source: str, destination: str, theme_dir: Path | None = None) -> Path:
    directory = Path(theme_dir or _default_theme_dir()).expanduser()
    src = directory / f"{safe_theme_name(source)}.json"
    dst = directory / f"{safe_theme_name(destination)}.json"
    if dst.exists():
        raise EditorError(f"Theme already exists: {destination}")
    data = ensure_theme_schema(json.loads(src.read_text(encoding="utf-8")))
    _atomic_write(dst, dump_json(data))
    return dst


def rename_theme(source: str, destination: str, theme_dir: Path | None = None) -> Path:
    directory = Path(theme_dir or _default_theme_dir()).expanduser()
    src = directory / f"{safe_theme_name(source)}.json"
    dst = directory / f"{safe_theme_name(destination)}.json"
    if not src.exists():
        raise EditorError(f"Theme not found: {source}")
    if dst.exists():
        raise EditorError(f"Theme already exists: {destination}")
    os.replace(src, dst)
    return dst


def delete_theme(name: str, theme_dir: Path | None = None) -> Path:
    directory = Path(theme_dir or _default_theme_dir()).expanduser()
    path = directory / f"{safe_theme_name(name)}.json"
    if not path.exists():
        raise EditorError(f"Theme not found: {name}")
    trash = _state_dir() / "trash"
    trash.mkdir(parents=True, exist_ok=True)
    target = trash / f"{safe_theme_name(name)}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    shutil.move(path, target)
    return target
