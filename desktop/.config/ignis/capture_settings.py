"""Ignis-backed screenshot and OCR preferences."""

from __future__ import annotations

from typing import Any

from desktop_runtime.capture_config import (
    OCR_ENGINE_MODES,
    OCR_PAGE_SEGMENTATION_MODES,
    available_tesseract_languages,
    parse_ocr_languages,
    usable_ocr_languages,
)
from util import BindableSettings, JsonSettings


@JsonSettings("capture")
class CaptureSettings(BindableSettings):
    screenshot_save_to_disk: bool = True
    screenshot_copy_to_clipboard: bool = True
    ocr_languages: str = "eng"
    ocr_page_segmentation_mode: int = 3
    ocr_engine_mode: int = 3

    @staticmethod
    def migrate_settings(data: dict[str, Any]) -> dict[str, Any]:
        migrated = dict(data)
        migrated["screenshot_save_to_disk"] = (
            migrated.get("screenshot_save_to_disk", True) is True
        )
        migrated["screenshot_copy_to_clipboard"] = (
            migrated.get("screenshot_copy_to_clipboard", True) is True
        )

        languages = parse_ocr_languages(migrated.get("ocr_languages", "eng"))
        available = available_tesseract_languages()
        if available:
            languages = usable_ocr_languages(languages, available)
        migrated["ocr_languages"] = "+".join(languages or ["eng"])

        try:
            psm = int(migrated.get("ocr_page_segmentation_mode", 3))
        except (TypeError, ValueError):
            psm = 3
        migrated["ocr_page_segmentation_mode"] = (
            psm if psm in OCR_PAGE_SEGMENTATION_MODES else 3
        )

        try:
            oem = int(migrated.get("ocr_engine_mode", 3))
        except (TypeError, ValueError):
            oem = 3
        migrated["ocr_engine_mode"] = oem if oem in OCR_ENGINE_MODES else 3
        return migrated

    def set_screenshot_save_to_disk(self, value: bool) -> None:
        self.screenshot_save_to_disk = bool(value)

    def set_screenshot_copy_to_clipboard(self, value: bool) -> None:
        self.screenshot_copy_to_clipboard = bool(value)

    def selected_ocr_languages(self) -> list[str]:
        return parse_ocr_languages(self.ocr_languages)

    def update_ocr_languages(self, languages: list[str]) -> None:
        available = available_tesseract_languages()
        selected = usable_ocr_languages(languages, available)
        if selected:
            self.ocr_languages = "+".join(selected)

    def set_ocr_page_segmentation_mode(self, value: int) -> None:
        self.ocr_page_segmentation_mode = (
            value if value in OCR_PAGE_SEGMENTATION_MODES else 3
        )

    def set_ocr_engine_mode(self, value: int) -> None:
        self.ocr_engine_mode = value if value in OCR_ENGINE_MODES else 3


capture_settings = CaptureSettings()
