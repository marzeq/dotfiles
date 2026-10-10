"""Wallpaper and accent-colour integration."""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from pathlib import Path

from .process import run


IGNIS_DATA = Path.home() / ".local" / "share" / "ignis"
STYLE_SETTINGS = IGNIS_DATA / "settings" / "style.json"
DEFAULT_WALLPAPER = Path.home() / ".config" / "ignis" / "default_wallpaper.jpg"
WALLPAPER_LINK = Path.home() / ".local" / "state" / "wallpaper"
FIRST_START_MARKER = Path.home() / ".local" / "share" / "awww-first-start-done"
HEX_COLOUR = re.compile(r"^#[0-9a-fA-F]{6}$")


def _configured_wallpaper() -> Path:
    try:
        data = json.loads(STYLE_SETTINGS.read_text(encoding="utf-8"))
        configured = Path(os.path.expanduser(str(data.get("wallpaper", ""))))
        if configured.is_file():
            return configured
    except (OSError, ValueError, TypeError):
        pass
    return DEFAULT_WALLPAPER


def set_wallpaper(*, first_start: bool = False) -> None:
    if first_start and FIRST_START_MARKER.exists():
        return

    wallpaper = DEFAULT_WALLPAPER if first_start else _configured_wallpaper()
    WALLPAPER_LINK.parent.mkdir(parents=True, exist_ok=True)
    WALLPAPER_LINK.unlink(missing_ok=True)
    WALLPAPER_LINK.symlink_to(wallpaper)
    run(
        [
            "awww",
            "img",
            str(wallpaper),
            "--transition-fps=144",
            "--transition-step=128",
            "--transition-type=any",
        ]
    )
    if first_start:
        FIRST_START_MARKER.touch()


def _remove_if_symlink(path: Path) -> None:
    if path.is_symlink():
        path.unlink()


def _write_accent_files(colour: str) -> None:
    IGNIS_DATA.mkdir(parents=True, exist_ok=True)
    (IGNIS_DATA / "accent.scss").write_text(f"$accent: {colour};\n", encoding="utf-8")
    (IGNIS_DATA / "gtk-accent.css").write_text(
        f":root {{ --accent-bg-color: {colour}; }}\n", encoding="utf-8"
    )
    (IGNIS_DATA / "accent.txt").write_text(
        colour.removeprefix("#"), encoding="utf-8"
    )


def set_accent(colour: str) -> None:
    if HEX_COLOUR.fullmatch(colour) is None:
        raise ValueError("Accent colour must use the #RRGGBB format")

    gtk3_file = Path.home() / ".config" / "gtk-3.0" / "gtk.css"
    gtk4_file = Path.home() / ".config" / "gtk-4.0" / "gtk.css"
    for assets in (
        Path.home() / ".config" / "gtk-3.0" / "assets",
        Path.home() / ".config" / "gtk-4.0" / "assets",
    ):
        _remove_if_symlink(assets)

    backup_suffix = f".{int(time.time())}.bak"
    for gtk_file in (gtk3_file, gtk4_file):
        if gtk_file.is_symlink():
            gtk_file.unlink()
        elif gtk_file.is_file() and not any(
            gtk_file.parent.glob(f"{gtk_file.name}.*.bak")
        ):
            shutil.copy2(gtk_file, gtk_file.with_name(gtk_file.name + backup_suffix))
        gtk_file.parent.mkdir(parents=True, exist_ok=True)

    gtk4_file.write_text(
        f":root {{ --accent-bg-color: {colour}; }}\n", encoding="utf-8"
    )
    gtk3_file.write_text(f"@define-color accent_bg_color {colour};\n", encoding="utf-8")
    _write_accent_files(colour)


def _restore_latest_backup(path: Path) -> None:
    backups = sorted(
        path.parent.glob(f"{path.name}.*.bak"),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )
    if backups:
        shutil.copy2(backups[0], path)
    else:
        path.unlink(missing_ok=True)


def restore_accent() -> None:
    for assets in (
        Path.home() / ".config" / "gtk-3.0" / "assets",
        Path.home() / ".config" / "gtk-4.0" / "assets",
    ):
        _remove_if_symlink(assets)
    _restore_latest_backup(Path.home() / ".config" / "gtk-3.0" / "gtk.css")
    _restore_latest_backup(Path.home() / ".config" / "gtk-4.0" / "gtk.css")
    IGNIS_DATA.mkdir(parents=True, exist_ok=True)
    (IGNIS_DATA / "accent.scss").write_text("", encoding="utf-8")
    (IGNIS_DATA / "gtk-accent.css").write_text(
        ":root { --accent-bg-color: var(--accent-blue); }\n", encoding="utf-8"
    )
    (IGNIS_DATA / "accent.txt").write_text("", encoding="utf-8")
