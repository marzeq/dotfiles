"""Audio and media-key actions."""

from __future__ import annotations

import re

from .process import run, spawn


SINK = "@DEFAULT_AUDIO_SINK@"
SOURCE = "@DEFAULT_AUDIO_SOURCE@"


def _show_osd() -> None:
    spawn(["goignis", "open-window", "ignis_osd"])


def volume_up(step: int) -> None:
    run(["wpctl", "set-mute", SINK, "0"])
    run(["wpctl", "set-volume", SINK, f"{step}%+", "-l", "1.0"])
    _show_osd()


def volume_down(step: int) -> None:
    run(["wpctl", "set-volume", SINK, f"{step}%-"])
    result = run(["wpctl", "get-volume", SINK], capture_output=True)
    match = re.search(r"Volume:\s*([0-9.]+)", result.stdout)
    if match is not None and float(match.group(1)) <= 0:
        run(["wpctl", "set-mute", SINK, "1"])
    _show_osd()


def toggle_output_mute() -> None:
    run(["wpctl", "set-mute", SINK, "toggle"])
    _show_osd()


def toggle_input_mute() -> None:
    run(["wpctl", "set-mute", SOURCE, "toggle"])


def player(action: str) -> None:
    run(["playerctl", action])
