"""Shared definitions and serialization for GUI-managed Hyprland options."""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Iterable
from typing import Any


OPTIONS_PATH = Path(os.path.expanduser("~/.local/share/ignis/opts.lua"))
LEGACY_OPTIONS_PATH = Path(os.path.expanduser("~/.config/hypr/opts.lua"))
MODIFIER_KEYS = ("SHIFT", "CTRL", "ALT", "SUPER")
MOD_KEYS = ("SUPER", "ALT", "CTRL", "SHIFT")
BASE_KEYS = (
    *(chr(value) for value in range(ord("A"), ord("Z") + 1)),
    *(str(value) for value in range(10)),
    *(f"F{value}" for value in range(1, 25)),
    "RETURN",
    "SPACE",
    "TAB",
    "ESCAPE",
    "BACKSPACE",
    "DELETE",
    "INSERT",
    "HOME",
    "END",
    "PAGE_UP",
    "PAGE_DOWN",
    "left",
    "right",
    "up",
    "down",
    "minus",
    "equal",
    "bracketleft",
    "bracketright",
    "backslash",
    "semicolon",
    "apostrophe",
    "grave",
    "comma",
    "period",
    "slash",
    *(f"KP_{value}" for value in range(10)),
    "KP_Add",
    "KP_Subtract",
    "KP_Multiply",
    "KP_Divide",
    "KP_Enter",
)


@dataclass(frozen=True)
class Keybind:
    enabled: bool
    modifiers: tuple[str, ...]
    key: str


@dataclass(frozen=True)
class KeybindDefinition:
    action: str
    label: str
    category: str
    default: Keybind


def _binding(
    action: str,
    label: str,
    category: str,
    key: str,
    *,
    primary_modifier: str | None = "SUPER",
    modifiers: tuple[str, ...] = (),
) -> KeybindDefinition:
    selected = (*modifiers, primary_modifier) if primary_modifier else modifiers
    concrete_modifiers = tuple(
        modifier for modifier in MODIFIER_KEYS if modifier in selected
    )
    return KeybindDefinition(
        action, label, category, Keybind(True, concrete_modifiers, key)
    )


KEYBIND_DEFINITIONS: tuple[KeybindDefinition, ...] = (
    _binding("close_window", "Close active window", "Windows", "Q"),
    _binding("toggle_floating", "Toggle floating", "Windows", "T"),
    _binding("toggle_layout", "Swap master / toggle split", "Windows", "S"),
    _binding("fullscreen", "Toggle fullscreen", "Windows", "F", modifiers=("SHIFT",)),
    _binding("focus_left_h", "Focus left (H)", "Focus", "H"),
    _binding("focus_down_j", "Focus down (J)", "Focus", "J"),
    _binding("focus_up_k", "Focus up (K)", "Focus", "K"),
    _binding("focus_right_l", "Focus right (L)", "Focus", "L"),
    _binding("focus_left_arrow", "Focus left (arrow)", "Focus", "left"),
    _binding("focus_down_arrow", "Focus down (arrow)", "Focus", "down"),
    _binding("focus_up_arrow", "Focus up (arrow)", "Focus", "up"),
    _binding("focus_right_arrow", "Focus right (arrow)", "Focus", "right"),
    _binding("move_up_h", "Move window up (H)", "Move windows", "H", modifiers=("SHIFT",)),
    _binding("move_down_j", "Move window down (J)", "Move windows", "J", modifiers=("SHIFT",)),
    _binding("move_left_k", "Move window left (K)", "Move windows", "K", modifiers=("SHIFT",)),
    _binding("move_right_l", "Move window right (L)", "Move windows", "L", modifiers=("SHIFT",)),
    _binding("move_up_arrow", "Move window up (arrow)", "Move windows", "left", modifiers=("SHIFT",)),
    _binding("move_down_arrow", "Move window down (arrow)", "Move windows", "down", modifiers=("SHIFT",)),
    _binding("move_left_arrow", "Move window left (arrow)", "Move windows", "up", modifiers=("SHIFT",)),
    _binding("move_right_arrow", "Move window right (arrow)", "Move windows", "right", modifiers=("SHIFT",)),
    _binding("open_file_manager", "Open file manager", "Applications", "F"),
    _binding("open_terminal", "Open terminal", "Applications", "RETURN"),
    _binding("open_browser", "Open browser", "Applications", "B"),
    _binding("open_launcher", "Open launcher", "Shell", "SPACE"),
    _binding("keyboard_layout", "Choose keyboard layout", "Shell", "SPACE", primary_modifier=None, modifiers=("ALT",)),
    _binding("notifications", "Toggle notifications", "Shell", "N"),
    _binding("screenshot_area", "Capture area", "Screenshots and tools", "S", modifiers=("SHIFT",)),
    _binding("screenshot_window", "Capture window", "Screenshots and tools", "W", modifiers=("SHIFT",)),
    _binding("screenshot_monitor", "Capture monitor", "Screenshots and tools", "M", modifiers=("SHIFT",)),
    _binding("ocr", "Recognise text on screen", "Screenshots and tools", "T", modifiers=("SHIFT",)),
    _binding("colour_picker", "Pick a colour", "Screenshots and tools", "C", modifiers=("SHIFT",)),
    *tuple(
        _binding(f"workspace_{number}", f"Switch to workspace {number}", "Workspaces", "0" if number == 10 else str(number))
        for number in range(1, 11)
    ),
    *tuple(
        _binding(
            f"move_to_workspace_{number}",
            f"Move window to workspace {number}",
            "Workspaces",
            "0" if number == 10 else str(number),
            modifiers=("SHIFT",),
        )
        for number in range(1, 11)
    ),
    *tuple(
        _binding(
            f"focus_monitor_{number}",
            f"Focus monitor {number}",
            "Monitors",
            "0" if number == 10 else str(number),
            primary_modifier="ALT",
        )
        for number in range(1, 11)
    ),
    *tuple(
        _binding(
            f"move_to_monitor_{number}",
            f"Move window to monitor {number}",
            "Monitors",
            "0" if number == 10 else str(number),
            primary_modifier="ALT",
            modifiers=("SHIFT",),
        )
        for number in range(1, 11)
    ),
)

def keybind_definitions(
    monitor_numbers: int | Iterable[int],
    workspace_count: int = 10,
) -> tuple[KeybindDefinition, ...]:
    """Return bindings relevant to the currently connected monitor set."""
    active_monitors = (
        set(range(1, monitor_numbers + 1))
        if isinstance(monitor_numbers, int)
        else set(monitor_numbers)
    )
    return tuple(
        definition
        for definition in KEYBIND_DEFINITIONS
        if (
            definition.category != "Monitors"
            or int(definition.action.rsplit("_", 1)[1]) in active_monitors
        )
        and (
            definition.category != "Workspaces"
            or int(definition.action.rsplit("_", 1)[1]) <= workspace_count
        )
    )


def default_keybindings_json(
    definitions: tuple[KeybindDefinition, ...] = KEYBIND_DEFINITIONS,
) -> str:
    return json.dumps(
        {item.action: asdict(item.default) for item in definitions},
        separators=(",", ":"),
        sort_keys=True,
    )


def parse_keybindings(
    value: str,
    definitions: tuple[KeybindDefinition, ...] = KEYBIND_DEFINITIONS,
    *,
    mod1: str = "SUPER",
    mod2: str = "ALT",
) -> dict[str, Keybind]:
    try:
        raw = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        raw = {}
    result: dict[str, Keybind] = {}
    for definition in definitions:
        item = raw.get(definition.action, {})
        raw_modifiers = item.get("modifiers", definition.default.modifiers)
        selected = [
            modifier
            for modifier in raw_modifiers
            if modifier in MODIFIER_KEYS
        ]
        legacy_mod = item.get("mod")
        if legacy_mod == "mod1" and mod1 in MODIFIER_KEYS:
            selected.append(mod1)
        elif legacy_mod == "mod2" and mod2 in MODIFIER_KEYS:
            selected.append(mod2)
        modifiers = tuple(
            modifier for modifier in MODIFIER_KEYS if modifier in selected
        )
        key = str(item.get("key", definition.default.key)).strip()
        if key not in BASE_KEYS:
            key = definition.default.key
        enabled = item.get("enabled", definition.default.enabled)
        if not isinstance(enabled, bool):
            enabled = definition.default.enabled
        result[definition.action] = Keybind(enabled, modifiers, key)
    return result


def serialize_keybindings(
    values: dict[str, Keybind],
    definitions: tuple[KeybindDefinition, ...] = KEYBIND_DEFINITIONS,
) -> str:
    return json.dumps(
        {
            definition.action: asdict(
                values.get(definition.action, definition.default)
            )
            for definition in definitions
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def legacy_options() -> dict[str, Any]:
    """Read the small supported subset of the old hand-written opts.lua."""
    try:
        contents = LEGACY_OPTIONS_PATH.read_text()
    except OSError:
        return {}
    result: dict[str, Any] = {}
    programs_match = re.search(r"programs\s*=\s*\{(.*?)\}", contents, re.S)
    if programs_match:
        for lua_name, setting_name in (
            ("terminal", "program_terminal"),
            ("fileManager", "program_file_manager"),
            ("menu", "program_menu"),
            ("browser", "program_browser"),
            ("editor", "program_editor"),
        ):
            match = re.search(
                rf"\b{lua_name}\s*=\s*(['\"])(.*?)\1", programs_match[1]
            )
            if match:
                result[setting_name] = match[2]
    for lua_name, setting_name in (("mod", "mod1"), ("mod2", "mod2")):
        match = re.search(rf"\b{lua_name}\s*=\s*(['\"])(.*?)\1", contents)
        if match and match[2] in MOD_KEYS:
            result[setting_name] = match[2]
    return result


def _lua_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_options(
    *,
    programs: dict[str, str],
    keybindings: dict[str, Keybind],
    workspaces_span_displays: bool,
    workspace_count: int,
    primary_monitor: str,
    layout_type: str,
    definitions: tuple[KeybindDefinition, ...] = KEYBIND_DEFINITIONS,
) -> str:
    lines = [
        "-- Generated by Ignis Settings. Manual changes may be overwritten.",
        "return {",
        f"  workspaces_span_displays = {str(workspaces_span_displays).lower()},",
        f"  workspace_count = {workspace_count},",
        f"  primary_monitor = {_lua_string(primary_monitor)},",
        f"  layout_type = {_lua_string(layout_type)},",
        "  programs = {",
    ]
    for name, value in programs.items():
        lines.append(f"    {name} = {_lua_string(value)},")
    lines.extend(["  },", "  keybindings = {"])
    for definition in definitions:
        binding = keybindings[definition.action]
        modifiers = ", ".join(_lua_string(value) for value in binding.modifiers)
        lines.extend(
            [
                f"    [{_lua_string(definition.action)}] = {{",
                f"      enabled = {str(binding.enabled).lower()},",
                f"      modifiers = {{{modifiers}}},",
                f"      key = {_lua_string(binding.key)},",
                "    },",
            ]
        )
    lines.extend(["  },", "}", ""])
    return "\n".join(lines)


def write_atomic(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, 0o644)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
