"""Screenshot and OCR actions."""

from __future__ import annotations

import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from .process import run, spawn


SCREENSHOT_MODES = {
    "area": "region",
    "monitor": "output",
    "window": "window",
}


def screenshot(mode: str) -> None:
    output_dir = Path.home() / "pictures" / "screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")[:-3] + ".png"
    output_path = output_dir / filename

    run(
        [
            "hyprshot",
            "-szm",
            SCREENSHOT_MODES[mode],
            "-o",
            str(output_dir),
            "-f",
            filename,
        ],
        capture_output=True,
    )
    if not output_path.is_file():
        raise RuntimeError(f"Screenshot was not created: {output_path}")

    notification = run(
        [
            "notify-send",
            f"--icon={output_path}",
            "--app-name=Screenshot",
            "-A",
            "open=Open",
            "Screenshot saved",
            filename,
        ],
        capture_output=True,
    )
    if notification.stdout.strip() == "open":
        spawn(["xdg-open", str(output_path)])


def ocr() -> None:
    with tempfile.TemporaryDirectory(prefix="hypr-ocr-") as directory:
        image_path = Path(directory) / "capture.png"
        output_base = Path(directory) / "text"
        run(
            [
                "hyprshot",
                "-szm",
                "region",
                "-f",
                image_path.name,
                "-o",
                directory,
                "--silent",
            ]
        )
        run(["mogrify", "-modulate", "100,0", "-resize", "400%", str(image_path)])
        run(
            ["tesseract", str(image_path), str(output_base)],
            capture_output=True,
        )
        text_path = output_base.with_suffix(".txt")
        try:
            text = text_path.read_text(encoding="utf-8").rstrip("\n")
        except OSError as error:
            raise RuntimeError(f"Could not read OCR output: {error}") from error
        try:
            subprocess.run(["wl-copy"], check=True, input=text, text=True)
        except FileNotFoundError as error:
            raise RuntimeError("Required command not found: wl-copy") from error
        except subprocess.CalledProcessError as error:
            raise RuntimeError("Could not copy OCR output to the clipboard") from error
