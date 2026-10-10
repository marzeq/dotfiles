"""Argument parsing for the desktop command entry point."""

from __future__ import annotations

import argparse
import sys

from . import appearance, capture, media, network, session, startup, workspaces


def _positive_integer(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _workspace_number(value: str) -> int:
    number = int(value)
    if not 1 <= number <= 10:
        raise argparse.ArgumentTypeError("must be between 1 and 10")
    return number


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="desktop-cli")
    commands = root.add_subparsers(dest="command", required=True)

    audio = commands.add_parser("audio")
    audio_actions = audio.add_subparsers(dest="action", required=True)
    for name in ("volume-up", "volume-down"):
        volume = audio_actions.add_parser(name)
        volume.add_argument("step", nargs="?", type=_positive_integer, default=2)
    for name in (
        "mute-output",
        "mute-input",
        "play-pause",
        "play",
        "pause",
        "next",
        "previous",
        "stop",
    ):
        audio_actions.add_parser(name)

    screenshot = commands.add_parser("screenshot")
    screenshot.add_argument("mode", choices=sorted(capture.SCREENSHOT_MODES))
    commands.add_parser("ocr")

    wallpaper = commands.add_parser("wallpaper")
    wallpaper.add_argument("--first-start", action="store_true")

    workspace = commands.add_parser("workspace")
    workspace.add_argument("action", choices=("move", "switch"))
    workspace.add_argument("number", type=_workspace_number)

    accent = commands.add_parser("accent")
    accent.add_argument("action", choices=("restore", "set"))
    accent.add_argument("colour", nargs="?")

    commands.add_parser("autostart")
    commands.add_parser("restart-hypridle")
    commands.add_parser("toggle-ethernet")
    return root


def _audio(action: str, step: int | None) -> None:
    if action == "volume-up":
        media.volume_up(step or 2)
    elif action == "volume-down":
        media.volume_down(step or 2)
    elif action == "mute-output":
        media.toggle_output_mute()
    elif action == "mute-input":
        media.toggle_input_mute()
    else:
        media.player(action)


def main() -> None:
    arguments = parser().parse_args()
    try:
        if arguments.command == "audio":
            _audio(arguments.action, getattr(arguments, "step", None))
        elif arguments.command == "screenshot":
            capture.screenshot(arguments.mode)
        elif arguments.command == "ocr":
            capture.ocr()
        elif arguments.command == "wallpaper":
            appearance.set_wallpaper(first_start=arguments.first_start)
        elif arguments.command == "workspace":
            getattr(workspaces, arguments.action)(arguments.number)
        elif arguments.command == "accent":
            if arguments.action == "set":
                if arguments.colour is None:
                    raise ValueError("accent set requires a colour")
                appearance.set_accent(arguments.colour)
            else:
                appearance.restore_accent()
        elif arguments.command == "autostart":
            startup.launch_xdg_autostart()
        elif arguments.command == "restart-hypridle":
            session.restart_hypridle()
        elif arguments.command == "toggle-ethernet":
            network.toggle_ethernet()
    except (RuntimeError, ValueError) as error:
        print(f"desktop-cli: {error}", file=sys.stderr)
        raise SystemExit(1) from error
