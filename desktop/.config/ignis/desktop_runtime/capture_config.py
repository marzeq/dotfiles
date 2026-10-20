"""Shared screenshot and OCR settings without an Ignis dependency."""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CAPTURE_SETTINGS_PATH = (
    Path.home() / ".local" / "share" / "ignis" / "settings" / "capture.json"
)

OCR_PAGE_SEGMENTATION_MODES = {
    3: "Automatic",
    4: "Single column",
    6: "Single text block",
    7: "Single line",
    8: "Single word",
    11: "Sparse text",
    12: "Sparse text with orientation detection",
    13: "Raw line",
}

OCR_ENGINE_MODES = {
    3: "Automatic",
    1: "LSTM neural network",
}

_TESSDATA_DIRECTORY_PATTERN = re.compile(
    r'List of available languages in "([^"]+)"'
)


@dataclass(frozen=True)
class CaptureConfig:
    screenshot_save_to_disk: bool = True
    screenshot_copy_to_clipboard: bool = True
    ocr_languages: tuple[str, ...] = ("eng",)
    ocr_page_segmentation_mode: int = 3
    ocr_engine_mode: int = 3


def available_tesseract_languages() -> list[str]:
    """Return language identifiers reported by the installed Tesseract."""
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    languages: list[str] = []
    for line in result.stdout.splitlines():
        language = line.strip()
        if (
            not language
            or language == "osd"
            or language.startswith("List of available languages")
        ):
            continue
        languages.append(language)
    return sorted(set(languages))


def tesseract_data_directories() -> list[Path]:
    """Return existing model directories worth monitoring for changes."""
    candidates: list[Path] = []
    configured = os.environ.get("TESSDATA_PREFIX")
    if configured:
        candidates.append(Path(configured).expanduser())

    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        result = None
    if result is not None:
        match = _TESSDATA_DIRECTORY_PATTERN.search(
            f"{result.stdout}\n{result.stderr}"
        )
        if match:
            candidates.append(Path(match.group(1)))

    candidates.extend(
        [
            Path("/usr/share/tessdata"),
            Path("/usr/local/share/tessdata"),
            Path.home() / ".local" / "share" / "tessdata",
        ]
    )
    return list(dict.fromkeys(path for path in candidates if path.is_dir()))


def parse_ocr_languages(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = value.split("+")
    elif isinstance(value, list):
        candidates = value
    else:
        candidates = []
    return list(
        dict.fromkeys(
            language.strip()
            for language in candidates
            if isinstance(language, str) and language.strip()
        )
    )


def usable_ocr_languages(configured: Any, available: list[str]) -> list[str]:
    selected = [
        language
        for language in parse_ocr_languages(configured)
        if language in available
    ]
    if selected:
        return selected
    if "eng" in available:
        return ["eng"]
    return available[:1]


def _choice(value: Any, choices: dict[int, str], fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed in choices else fallback


def load_capture_config(*, validate_languages: bool = True) -> CaptureConfig:
    try:
        raw = json.loads(CAPTURE_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raw = {}
    if not isinstance(raw, dict):
        raw = {}

    configured_languages = raw.get("ocr_languages", "eng")
    if validate_languages:
        available = available_tesseract_languages()
        languages = usable_ocr_languages(configured_languages, available)
    else:
        languages = parse_ocr_languages(configured_languages)
    if not languages:
        languages = parse_ocr_languages(configured_languages) or ["eng"]

    return CaptureConfig(
        screenshot_save_to_disk=raw.get("screenshot_save_to_disk", True) is True,
        screenshot_copy_to_clipboard=(
            raw.get("screenshot_copy_to_clipboard", True) is True
        ),
        ocr_languages=tuple(languages),
        ocr_page_segmentation_mode=_choice(
            raw.get("ocr_page_segmentation_mode", 3),
            OCR_PAGE_SEGMENTATION_MODES,
            3,
        ),
        ocr_engine_mode=_choice(
            raw.get("ocr_engine_mode", 3), OCR_ENGINE_MODES, 3
        ),
    )
