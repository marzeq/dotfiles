"""XKB keyboard layout and variant display-name helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

XKB_RULES_PATH = "/usr/share/X11/xkb/rules/base.lst"


@dataclass(frozen=True)
class KeyboardChoice:
    value: str
    label: str


@dataclass(frozen=True)
class KeyboardLayoutConfig:
    layout: str
    variant: str = ""


def parse_xkb_rules(
    text: str,
) -> tuple[list[KeyboardChoice], dict[str, list[KeyboardChoice]]]:
    """Parse layout and variant codes with their human-readable XKB names."""
    layouts: list[KeyboardChoice] = []
    variants: dict[str, list[KeyboardChoice]] = {}
    layout_codes: set[str] = set()
    section = ""

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("!"):
            heading = line[1:].strip().split(maxsplit=1)[0]
            section = heading if heading in {"layout", "variant"} else ""
            continue
        if not line or line.startswith("#"):
            continue

        if section == "layout":
            parts = line.split(maxsplit=1)
            if (
                len(parts) == 2
                and parts[0] != "custom"
                and parts[0] not in layout_codes
            ):
                layouts.append(KeyboardChoice(value=parts[0], label=parts[1]))
                layout_codes.add(parts[0])
        elif section == "variant":
            parts = line.split(maxsplit=2)
            if len(parts) == 3 and parts[1].endswith(":"):
                layout = parts[1][:-1]
                variants.setdefault(layout, []).append(
                    KeyboardChoice(value=parts[0], label=parts[2])
                )

    return layouts, variants


@lru_cache(maxsize=1)
def _keyboard_choices() -> tuple[
    list[KeyboardChoice], dict[str, list[KeyboardChoice]]
]:
    try:
        with open(XKB_RULES_PATH, encoding="utf-8") as rules_file:
            return parse_xkb_rules(rules_file.read())
    except OSError:
        return [], {}


def get_keyboard_layouts() -> list[KeyboardChoice]:
    return list(_keyboard_choices()[0])


def get_keyboard_variants(layout: str) -> list[KeyboardChoice]:
    return [
        KeyboardChoice(value="", label="Default"),
        *_keyboard_choices()[1].get(layout, []),
    ]


def parse_keyboard_config(
    layouts: str, variants: str
) -> list[KeyboardLayoutConfig]:
    """Parse Hyprland's comma-separated keyboard layout configuration."""
    layout_codes = [code.strip() for code in layouts.split(",") if code.strip()]
    variant_codes = [code.strip() for code in variants.split(",")]
    return [
        KeyboardLayoutConfig(
            layout=layout,
            variant=variant_codes[index] if index < len(variant_codes) else "",
        )
        for index, layout in enumerate(layout_codes)
    ]


def serialize_keyboard_config(
    entries: list[KeyboardLayoutConfig],
) -> tuple[str, str]:
    """Serialize entries while retaining empty variants between layouts."""
    return (
        ",".join(entry.layout for entry in entries),
        ",".join(entry.variant for entry in entries),
    )


def keyboard_config_label(entry: KeyboardLayoutConfig) -> str:
    choices = (
        get_keyboard_variants(entry.layout)
        if entry.variant
        else get_keyboard_layouts()
    )
    value = entry.variant or entry.layout
    return next((choice.label for choice in choices if choice.value == value), value)


def active_layout_code(
    active_keymap: str, entries: list[KeyboardLayoutConfig]
) -> str:
    """Resolve Hyprland's active keymap name back to its configured code."""
    for entry in entries:
        if keyboard_config_label(entry).casefold() == active_keymap.casefold():
            return entry.layout
    return entries[0].layout if entries else ""
