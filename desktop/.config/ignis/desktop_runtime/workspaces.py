"""Deterministic logical-workspace controller for Hyprland."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .process import run


SETTINGS_PATH = Path.home() / ".local" / "share" / "ignis" / "workspace-state.json"
ACTIVE_WORKSPACE_PATH = (
    Path.home() / ".local" / "share" / "ignis" / "active-logical-workspace"
)


def _json_command(command: str) -> Any:
    result = run(["hyprctl", command, "-j"], capture_output=True)
    return json.loads(result.stdout)


def _settings() -> dict[str, Any]:
    try:
        value = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def workspace_plan(
    monitors: list[dict[str, Any]], primary_name: str
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, Any]]:
    ordered = sorted(monitors, key=lambda monitor: int(monitor.get("id", 0)))
    if not ordered:
        raise RuntimeError("Hyprland has no active monitors")
    primary = next(
        (monitor for monitor in ordered if monitor.get("name") == primary_name),
        ordered[0],
    )
    offsets = {str(primary["name"]): 0}
    block = 1
    for monitor in ordered:
        name = str(monitor["name"])
        if name != primary["name"]:
            offsets[name] = block * 10
            block += 1
    return ordered, offsets, primary


def _logical_id(logical: int, monitor: dict[str, Any], offsets: dict[str, int]) -> int:
    return offsets[str(monitor["name"])] + logical


def _dispatch_batch(commands: list[str]) -> None:
    result = run(
        ["hyprctl", "--batch", " ; ".join(commands)],
        capture_output=True,
    )
    combined = result.stdout + result.stderr
    if "error:" in combined.lower():
        raise RuntimeError(combined.strip())


def _lua_string(value: object) -> str:
    return json.dumps(str(value))


def _publish_active_workspace(logical: int) -> None:
    ACTIVE_WORKSPACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{ACTIVE_WORKSPACE_PATH.name}.",
        dir=ACTIVE_WORKSPACE_PATH.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(f"{logical}\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, ACTIVE_WORKSPACE_PATH)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def switch(logical: int) -> None:
    settings = _settings()
    cursor = _json_command("cursorpos")
    cursor_x = int(cursor["x"])
    cursor_y = int(cursor["y"])
    monitors, offsets, primary = workspace_plan(
        _json_command("monitors"), str(settings.get("primary_monitor", ""))
    )
    focused = next(
        (monitor for monitor in monitors if monitor.get("focused") is True),
        primary,
    )
    targets = (
        monitors if settings.get("workspaces_span_displays") is True else [primary]
    )
    commands: list[str] = []
    for monitor in targets:
        commands.extend(
            [
                "dispatch hl.dsp.focus({ monitor = "
                f"{_lua_string(monitor['name'])} }})",
                "dispatch hl.dsp.focus({ workspace = "
                f"{_lua_string(_logical_id(logical, monitor, offsets))} }})",
            ]
        )
    commands.append(
        "dispatch hl.dsp.focus({ monitor = " f"{_lua_string(focused['name'])} }})"
    )
    commands.append(
        "dispatch hl.dsp.cursor.move({ " f"x = {cursor_x}, y = {cursor_y} }})"
    )
    _dispatch_batch(commands)
    _publish_active_workspace(logical)


def move(logical: int) -> None:
    settings = _settings()
    monitors, offsets, primary = workspace_plan(
        _json_command("monitors"), str(settings.get("primary_monitor", ""))
    )
    focused = next(
        (monitor for monitor in monitors if monitor.get("focused") is True),
        primary,
    )
    target = focused if settings.get("workspaces_span_displays") is True else primary
    _dispatch_batch(
        [
            "dispatch hl.dsp.window.move({ workspace = "
            f"{_lua_string(_logical_id(logical, target, offsets))}, "
            "follow = false })"
        ]
    )
