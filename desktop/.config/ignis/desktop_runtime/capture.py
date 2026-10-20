"""Screenshot and OCR actions."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from .capture_config import load_capture_config
from .process import run, spawn


SCREENSHOT_MODES = {
    "area": "area",
    "monitor": "monitor",
    "window": "window",
}


@contextmanager
def _frozen_screen() -> Iterator[None]:
    try:
        freeze = subprocess.Popen(
            ["hyprpicker", "-r", "-z"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError("Required command not found: hyprpicker") from error

    try:
        # Give hyprpicker enough time to map its frozen-screen surface before
        # the selection overlay starts accepting input.
        time.sleep(0.2)
        yield
    finally:
        if freeze.poll() is None:
            freeze.terminate()
        try:
            freeze.wait(timeout=1)
        except subprocess.TimeoutExpired:
            freeze.kill()
            freeze.wait()


def _json_command(command: list[str]) -> object:
    result = run(command, capture_output=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid JSON from {command[0]}") from error


def _visible_window_boxes() -> str:
    monitors = _json_command(["hyprctl", "-j", "monitors"])
    clients = _json_command(["hyprctl", "-j", "clients"])
    if not isinstance(monitors, list) or not isinstance(clients, list):
        raise RuntimeError("Could not query visible Hyprland windows")

    active_workspaces = {
        monitor.get("activeWorkspace", {}).get("id")
        for monitor in monitors
        if isinstance(monitor, dict)
    }
    boxes: list[str] = []
    for client in clients:
        if not isinstance(client, dict):
            continue
        workspace = client.get("workspace")
        position = client.get("at")
        size = client.get("size")
        if (
            not isinstance(workspace, dict)
            or workspace.get("id") not in active_workspaces
            or client.get("mapped") is not True
            or client.get("hidden") is True
            or not isinstance(position, list)
            or len(position) != 2
            or not isinstance(size, list)
            or len(size) != 2
        ):
            continue
        boxes.append(f"{position[0]},{position[1]} {size[0]}x{size[1]}")

    if not boxes:
        raise RuntimeError("There are no visible windows to capture")
    return "\n".join(boxes) + "\n"


def _select_geometry(mode: str) -> str:
    if mode == "area":
        command = ["slurp", "-d"]
        input_text = None
    elif mode == "monitor":
        command = ["slurp", "-o", "-r"]
        input_text = None
    elif mode == "window":
        command = ["slurp", "-r"]
        input_text = _visible_window_boxes()
    else:
        raise ValueError(f"Unknown screenshot mode: {mode}")

    geometry = run(
        command, capture_output=True, input_text=input_text
    ).stdout.strip()
    if not geometry:
        raise RuntimeError("No screenshot region was selected")
    return geometry


def _capture_image(mode: str, image_path: Path) -> None:
    with _frozen_screen():
        geometry = _select_geometry(mode)
        run(
            ["grim", "-g", geometry, str(image_path)],
            capture_output=True,
        )
    if not image_path.is_file():
        raise RuntimeError("Screenshot was not created")


def _copy_image(image_path: Path) -> None:
    try:
        with image_path.open("rb") as image:
            subprocess.run(
                ["wl-copy", "--type", "image/png"],
                check=True,
                stdin=image,
            )
    except FileNotFoundError as error:
        raise RuntimeError("Required command not found: wl-copy") from error
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Could not copy screenshot to the clipboard") from error


def screenshot(mode: str) -> None:
    config = load_capture_config(validate_languages=False)
    filename = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")[:-3] + ".png"

    with tempfile.TemporaryDirectory(prefix="hypr-screenshot-") as directory:
        image_path = Path(directory) / filename
        _capture_image(SCREENSHOT_MODES[mode], image_path)

        output_path: Path | None = None
        if config.screenshot_save_to_disk:
            output_dir = Path.home() / "pictures" / "screenshots"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / filename
            shutil.copyfile(image_path, output_path)

        if config.screenshot_copy_to_clipboard:
            _copy_image(image_path)

    if output_path is None:
        if config.screenshot_copy_to_clipboard:
            run(
                [
                    "notify-send",
                    "--app-name=Screenshot",
                    "Screenshot copied",
                    "The image is available on the clipboard.",
                ],
                capture_output=True,
            )
        return

    notification = run(
        [
            "notify-send",
            f"--icon={output_path}",
            "--app-name=Screenshot",
            "-A",
            "open=Open",
            "Screenshot saved",
            (
                f"{filename} · copied to clipboard"
                if config.screenshot_copy_to_clipboard
                else filename
            ),
        ],
        capture_output=True,
    )
    if notification.stdout.strip() == "open":
        spawn(["xdg-open", str(output_path)])


def ocr() -> None:
    config = load_capture_config()
    with tempfile.TemporaryDirectory(prefix="hypr-ocr-") as directory:
        image_path = Path(directory) / "capture.png"
        output_base = Path(directory) / "text"
        _capture_image("area", image_path)
        run(["mogrify", "-modulate", "100,0", "-resize", "400%", str(image_path)])
        run(
            [
                "tesseract",
                str(image_path),
                str(output_base),
                "-l",
                "+".join(config.ocr_languages),
                "--psm",
                str(config.ocr_page_segmentation_mode),
                "--oem",
                str(config.ocr_engine_mode),
            ],
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
