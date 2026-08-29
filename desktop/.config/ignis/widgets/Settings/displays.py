"""Native Hyprland display configuration for the Ignis settings window.

The editor intentionally keeps a draft separate from the running compositor
configuration.  Changes are only written when Apply is pressed and are rolled
back automatically unless the user confirms them.
"""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable

from gi.repository import Gdk, GLib, Gtk  # pyright: ignore[reportMissingModuleSource]
from ignis.widgets import Widget

import util


MONITORS_PATH = Path(os.path.expanduser("~/.config/hypr/monitors.lua"))
TRANSFORMS = [
    "Normal",
    "90° clockwise",
    "180°",
    "270° clockwise",
    "Flipped",
    "Flipped 90°",
    "Flipped 180°",
    "Flipped 270°",
]
SCALES = [1.0, 1.25, 1.333333, 1.5, 1.6, 1.75, 2.0, 2.5, 3.0]
MODE_RE = re.compile(r"^(\d+)x(\d+)@([0-9.]+)(?:Hz)?$")


def _number(value: Any, default: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mode_parts(mode: str) -> tuple[int, int, float]:
    match = MODE_RE.match(mode)
    if not match:
        return 1920, 1080, 60.0
    return int(match[1]), int(match[2]), float(match[3])


def _normalise_mode(mode: str) -> str:
    return mode.removesuffix("Hz")


@dataclass
class MonitorConfig:
    name: str
    description: str
    make: str
    model: str
    serial: str
    mode: str
    available_modes: list[str]
    x: int
    y: int
    scale: float
    transform: int
    enabled: bool = True
    mirror: str = ""
    vrr: int = 0
    bit_depth: int = 8
    wide_color: int = 0
    hdr: int = 0
    sdr_brightness: float = 1.0

    @property
    def logical_size(self) -> tuple[int, int]:
        width, height, _ = _mode_parts(self.mode)
        if self.transform in (1, 3, 5, 7):
            width, height = height, width
        return round(width / self.scale), round(height / self.scale)

    @classmethod
    def from_json(cls, item: dict[str, Any]) -> "MonitorConfig":
        width = int(item.get("width") or 1920)
        height = int(item.get("height") or 1080)
        refresh = _number(item.get("refreshRate"), 60)
        current = f"{width}x{height}@{refresh:.2f}"
        modes = [_normalise_mode(str(value)) for value in item.get("availableModes", [])]
        if modes:
            # Hyprland rounds the active refresh rate in monitor JSON. Pick the
            # advertised mode that describes the same timing when possible.
            same_size = [mode for mode in modes if _mode_parts(mode)[:2] == (width, height)]
            current = min(
                same_size or modes,
                key=lambda mode: abs(_mode_parts(mode)[2] - refresh),
            )
        fmt = str(item.get("currentFormat", ""))
        return cls(
            name=str(item.get("name", "Unknown")),
            description=str(item.get("description") or item.get("name") or "Display"),
            make=str(item.get("make", "")),
            model=str(item.get("model", "")),
            serial=str(item.get("serial", "")),
            mode=current,
            available_modes=modes or [current],
            x=int(item.get("x") or 0),
            y=int(item.get("y") or 0),
            scale=max(0.25, _number(item.get("scale"), 1)),
            transform=int(item.get("transform") or 0),
            enabled=not bool(item.get("disabled", False)),
            mirror=(
                ""
                if str(item.get("mirrorOf") or "").lower() in ("", "none")
                else str(item.get("mirrorOf"))
            ),
            vrr=int(item.get("vrr") or 0),
            bit_depth=10 if "10" in fmt else 8,
            # These JSON keys describe detected capabilities, not the current
            # EDID override. New drafts therefore retain Hyprland's safe auto
            # setting instead of forcing capability detection on or off.
            wide_color=0,
            hdr=0,
            sdr_brightness=_number(item.get("sdrBrightness"), 1),
        )

class DisplayLayout(Gtk.DrawingArea):
    """Small draggable map of Hyprland's logical coordinate space."""

    def __init__(self, changed: Callable[[str, int, int], None]):
        super().__init__()
        self.set_content_width(680)
        self.set_content_height(280)
        self.set_hexpand(True)
        self.add_css_class("settings-display-layout")
        self._configs: list[MonitorConfig] = []
        self._rects: dict[str, tuple[float, float, float, float]] = {}
        self._selected = ""
        self._changed = changed
        self._draw_scale = 0.1
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._needs_recenter = True
        self._last_pointer = (340.0, 140.0)
        self._drag_name = ""
        self._drag_origin = (0, 0)
        self._pan_origin = (0.0, 0.0)
        self.set_draw_func(self._draw)

        click = Gtk.GestureClick()
        click.set_button(Gdk.BUTTON_PRIMARY)
        click.connect("pressed", self._on_pressed)
        self.add_controller(click)
        drag = Gtk.GestureDrag()
        drag.set_button(Gdk.BUTTON_PRIMARY)
        drag.connect("drag-begin", self._on_drag_begin)
        drag.connect("drag-update", self._on_drag_update)
        drag.connect("drag-end", self._on_drag_end)
        self.add_controller(drag)
        pan = Gtk.GestureDrag()
        pan.set_button(Gdk.BUTTON_MIDDLE)
        pan.connect("drag-begin", self._on_pan_begin)
        pan.connect("drag-update", self._on_pan_update)
        self.add_controller(pan)
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        self.add_controller(motion)
        scroll = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.VERTICAL
            | Gtk.EventControllerScrollFlags.HORIZONTAL
        )
        scroll.connect("scroll", self._on_scroll)
        self.add_controller(scroll)

    def update(self, configs: list[MonitorConfig], selected: str) -> None:
        self._configs = configs
        self._selected = selected
        self.queue_draw()

    def request_recenter(self) -> None:
        self._needs_recenter = True
        self.queue_draw()

    def _visible(self) -> list[MonitorConfig]:
        return [config for config in self._configs if config.enabled and not config.mirror]

    def _recenter(self, width: int, height: int) -> None:
        visible = self._visible()
        if not visible:
            self._draw_scale = 0.1
            self._offset_x = width / 2
            self._offset_y = height / 2
            self._needs_recenter = False
            return
        left = min(config.x for config in visible)
        top = min(config.y for config in visible)
        right = max(config.x + config.logical_size[0] for config in visible)
        bottom = max(config.y + config.logical_size[1] for config in visible)
        span_w, span_h = max(1, right - left), max(1, bottom - top)
        padding = 30
        fit_scale = min(
            max(1, width - padding * 2) / span_w,
            max(1, height - padding * 2) / span_h,
        )
        # Large coordinate gaps may extend beyond the viewport. Do not shrink
        # real outputs into tiny, distorted hit targets just to show empty
        # virtual space between them.
        useful_scale = max(
            72 / max(1, min(config.logical_size)) for config in visible
        )
        self._draw_scale = max(0.01, min(1.0, max(fit_scale, useful_scale)))
        self._offset_x = width / 2 - ((left + right) / 2) * self._draw_scale
        self._offset_y = height / 2 - ((top + bottom) / 2) * self._draw_scale
        self._needs_recenter = False

    def _draw(self, _area, cr, width: int, height: int) -> None:
        style = self.get_style_context()
        colour = style.get_color()
        self._rects.clear()
        if self._needs_recenter:
            self._recenter(width, height)

        cr.set_source_rgba(colour.red, colour.green, colour.blue, 0.045)
        grid = 24
        for x in range(round(self._offset_x % grid), width, grid):
            cr.move_to(x, 0)
            cr.line_to(x, height)
        for y in range(round(self._offset_y % grid), height, grid):
            cr.move_to(0, y)
            cr.line_to(width, y)
        cr.set_line_width(1)
        cr.stroke()

        for config in self._visible():
            logical_w, logical_h = config.logical_size
            x = self._offset_x + config.x * self._draw_scale
            y = self._offset_y + config.y * self._draw_scale
            w = logical_w * self._draw_scale
            h = logical_h * self._draw_scale
            self._rects[config.name] = (x, y, w, h)
            selected = config.name == self._selected

            radius = min(10, w / 4, h / 4)
            cr.new_sub_path()
            cr.arc(x + w - radius, y + radius, radius, -math.pi / 2, 0)
            cr.arc(x + w - radius, y + h - radius, radius, 0, math.pi / 2)
            cr.arc(x + radius, y + h - radius, radius, math.pi / 2, math.pi)
            cr.arc(x + radius, y + radius, radius, math.pi, math.pi * 1.5)
            cr.close_path()
            if selected:
                cr.set_source_rgba(colour.red, colour.green, colour.blue, 0.22)
            else:
                cr.set_source_rgba(colour.red, colour.green, colour.blue, 0.10)
            cr.fill_preserve()
            cr.set_source_rgba(colour.red, colour.green, colour.blue, 0.85 if selected else 0.30)
            cr.set_line_width(3 if selected else 1)
            cr.stroke()

            cr.set_source_rgba(colour.red, colour.green, colour.blue, 0.95)
            cr.select_font_face("Sans", 0, 1)
            cr.set_font_size(14)
            ext = cr.text_extents(config.name)
            if w >= ext.width + 12 and h >= ext.height + 10:
                cr.move_to(
                    x + (w - ext.width) / 2,
                    y + (h - ext.height) / 2 - ext.y_bearing,
                )
                cr.show_text(config.name)

    def _monitor_at(self, x: float, y: float) -> str:
        for name, (rx, ry, rw, rh) in reversed(tuple(self._rects.items())):
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                return name
        return ""

    def _on_pressed(self, _gesture, _count, x, y) -> None:
        name = self._monitor_at(x, y)
        if name:
            self._selected = name
            config = next(item for item in self._configs if item.name == name)
            self._changed(name, config.x, config.y)
            self.queue_draw()

    def _on_drag_begin(self, gesture, x, y) -> None:
        self._drag_name = self._monitor_at(x, y)
        config = next((item for item in self._configs if item.name == self._drag_name), None)
        if config:
            self._selected = config.name
            self._drag_origin = config.x, config.y
            # Selection is delivered through the same callback without moving.
            self._changed(config.name, config.x, config.y)
        else:
            gesture.set_state(Gtk.EventSequenceState.DENIED)

    def _snap(self, name: str, x: int, y: int) -> tuple[int, int]:
        current = next(config for config in self._configs if config.name == name)
        width, height = current.logical_size
        threshold = max(12, round(16 / self._draw_scale))
        xs: list[int] = []
        ys: list[int] = []
        for other in self._visible():
            if other.name == name:
                continue
            ow, oh = other.logical_size
            xs.extend((other.x, other.x + ow, other.x - width, other.x + ow - width))
            ys.extend((other.y, other.y + oh, other.y - height, other.y + oh - height))
        nearest_x = min(xs, key=lambda value: abs(value - x), default=x)
        nearest_y = min(ys, key=lambda value: abs(value - y), default=y)
        if abs(nearest_x - x) <= threshold:
            x = nearest_x
        if abs(nearest_y - y) <= threshold:
            y = nearest_y
        return x, y

    def _on_drag_update(self, _gesture, dx, dy) -> None:
        if not self._drag_name:
            return
        x = round(self._drag_origin[0] + dx / self._draw_scale)
        y = round(self._drag_origin[1] + dy / self._draw_scale)
        x, y = self._snap(self._drag_name, x, y)
        self._changed(self._drag_name, x, y)

    def _on_drag_end(self, *_args) -> None:
        self._drag_name = ""

    def _on_pan_begin(self, *_args) -> None:
        self._pan_origin = self._offset_x, self._offset_y

    def _on_pan_update(self, _gesture, dx, dy) -> None:
        self._offset_x = self._pan_origin[0] + dx
        self._offset_y = self._pan_origin[1] + dy
        self.queue_draw()

    def _on_motion(self, _controller, x, y) -> None:
        self._last_pointer = x, y

    def _on_scroll(self, controller, dx, dy) -> bool:
        state = controller.get_current_event_state()
        if not state & Gdk.ModifierType.CONTROL_MASK:
            return False
        delta = dy if abs(dy) >= abs(dx) else dx
        if delta == 0:
            return True
        old_scale = self._draw_scale
        new_scale = max(0.01, min(1.0, old_scale * math.exp(-delta * 0.18)))
        pointer_x, pointer_y = self._last_pointer
        world_x = (pointer_x - self._offset_x) / old_scale
        world_y = (pointer_y - self._offset_y) / old_scale
        self._draw_scale = new_scale
        self._offset_x = pointer_x - world_x * new_scale
        self._offset_y = pointer_y - world_y * new_scale
        self._needs_recenter = False
        self.queue_draw()
        return True


class DisplaySettings(Widget.Box):
    def __init__(self, primary_settings):
        self._primary_settings = primary_settings
        self._configs: list[MonitorConfig] = []
        self._selected = ""
        self._dirty = False
        self._syncing = False
        self._rollback_source = 0
        self._rollback_seconds = 0
        self._old_file: bytes | None = None
        self._old_primary = ""
        self._baseline_primary = primary_settings.primary_monitor
        self._draft_primary = primary_settings.primary_monitor
        self._signal_handlers: list[tuple[Any, int]] = []
        self._refresh_source = 0

        self._layout = DisplayLayout(self._layout_changed)
        self._monitor_picker = Gtk.DropDown.new_from_strings([])
        self._monitor_picker.add_css_class("settings-dropdown")
        self._monitor_picker.set_valign(Gtk.Align.CENTER)
        self._monitor_picker.set_hexpand(False)
        self._monitor_picker.connect("notify::selected", self._select_from_picker)
        self._details = Widget.Box(vertical=True)
        self._error = Widget.Label(
            halign="start", wrap=True, visible=False, css_classes=["settings-display-error"]
        )
        self._rollback_label = Widget.Label(label="", halign="start", hexpand=True)
        self._rollback = Widget.Revealer(
            reveal_child=False,
            transition_type="slide_down",
            child=Widget.Box(
                spacing=10,
                child=[
                    Widget.Icon(image="dialog-warning-symbolic", pixel_size=18),
                    self._rollback_label,
                    Widget.Button(
                        label="Revert",
                        css_classes=["settings-secondary-button"],
                        on_click=lambda *_: self._revert(),
                    ),
                    Widget.Button(
                        label="Keep changes",
                        css_classes=["settings-primary-button"],
                        on_click=lambda *_: self._keep(),
                    ),
                ],
                css_classes=["settings-display-confirm"],
            ),
        )
        self._apply_button = Widget.Button(
            label="Apply",
            sensitive=False,
            css_classes=["settings-primary-button"],
            on_click=lambda *_: self._apply(),
        )

        super().__init__(
            vertical=True,
            spacing=14,
            child=[
                self._rollback,
                Widget.Box(
                    vertical=True,
                    spacing=10,
                    child=[
                        Widget.Box(
                            spacing=10,
                            child=[
                                Widget.Box(
                                    vertical=True,
                                    hexpand=True,
                                    child=[
                                        Widget.Label(
                                            label="Arrange displays",
                                            halign="start",
                                            css_classes=["settings-display-card-title"],
                                        ),
                                        Widget.Label(
                                            label="Drag outputs · Middle-drag to pan · Ctrl+scroll to zoom.",
                                            halign="start",
                                            css_classes=["settings-row-subtitle"],
                                        ),
                                    ],
                                ),
                                Widget.Button(
                                    child=Widget.Box(
                                        spacing=6,
                                        child=[
                                            Widget.Icon(image="view-refresh-symbolic", pixel_size=14),
                                            Widget.Label(label="Refresh"),
                                        ],
                                    ),
                                    css_classes=["settings-secondary-button"],
                                    on_click=lambda *_: self.refresh(),
                                ),
                            ],
                        ),
                        self._layout,
                    ],
                    css_classes=["settings-display-layout-card"],
                ),
                Widget.Box(
                    vertical=True,
                    spacing=0,
                    child=[
                        Widget.Box(
                            spacing=12,
                            child=[
                                Widget.Label(
                                    label="Configure", halign="start", hexpand=True,
                                    css_classes=["settings-display-card-title"],
                                ),
                                self._monitor_picker,
                            ],
                            css_classes=["settings-display-details-heading"],
                        ),
                        self._details,
                    ],
                    css_classes=["settings-display-details-card"],
                ),
                self._error,
                Widget.Box(
                    spacing=10,
                    halign="end",
                    child=[
                        Widget.Button(
                            label="Reset",
                            css_classes=["settings-secondary-button"],
                            on_click=lambda *_: self.refresh(),
                        ),
                        self._apply_button,
                    ],
                ),
            ],
            css_classes=["settings-displays"],
        )
        self.connect("unrealize", self._cleanup)
        try:
            handler = util.hyprland.connect("monitor-added", self._hardware_changed)
            self._signal_handlers.append((util.hyprland, handler))
            for monitor in util.hyprland.monitors:
                self._watch_monitor(monitor)
        except (AttributeError, TypeError):
            # A manual Refresh remains available on older Ignis versions.
            pass
        self.refresh()

    def _watch_monitor(self, monitor) -> None:
        try:
            handler = monitor.connect("removed", self._hardware_changed)
            self._signal_handlers.append((monitor, handler))
        except (AttributeError, TypeError):
            pass

    def _hardware_changed(self, _source, monitor=None, *_args) -> None:
        if monitor is not None and monitor is not _source:
            self._watch_monitor(monitor)
        elif _source is not util.hyprland:
            # A removed monitor object otherwise remains retained until the
            # settings window closes, which grows across dock/undock cycles.
            for watched, handler in tuple(self._signal_handlers):
                if watched is _source:
                    try:
                        watched.disconnect(handler)
                    except (TypeError, RuntimeError):
                        pass
                    self._signal_handlers.remove((watched, handler))
        if self._dirty or self._rollback_source:
            self._show_error(
                "Connected displays changed. Apply or reset the draft, then refresh the layout."
            )
            return
        if self._refresh_source:
            GLib.source_remove(self._refresh_source)
        self._refresh_source = GLib.timeout_add(300, self._refresh_after_hardware_change)

    def _refresh_after_hardware_change(self) -> bool:
        self._refresh_source = 0
        self.refresh()
        return False

    def _schedule_refresh(self, delay: int = 900) -> None:
        if self._refresh_source:
            GLib.source_remove(self._refresh_source)
        self._refresh_source = GLib.timeout_add(delay, self._refresh_after_hardware_change)

    def _query(self) -> list[MonitorConfig]:
        for command in ("j/monitors all", "j/monitors"):
            try:
                payload = util.hyprland.send_command(command)
                parsed = json.loads(payload)
                if isinstance(parsed, list) and parsed:
                    return self._merge_saved_overrides(
                        [MonitorConfig.from_json(value) for value in parsed]
                    )
            except Exception:
                continue
        # Ignis already mirrors active monitor state, so this also keeps the UI
        # useful on versions where `monitors all` is unavailable.
        values = []
        for monitor in util.hyprland.monitors:
            values.append(
                MonitorConfig.from_json(
                    {
                        "name": monitor.name,
                        "description": monitor.description,
                        "make": monitor.make,
                        "model": monitor.model,
                        "serial": monitor.serial,
                        "width": monitor.width,
                        "height": monitor.height,
                        "refreshRate": monitor.refresh_rate,
                        "x": monitor.x,
                        "y": monitor.y,
                        "scale": monitor.scale,
                        "transform": monitor.transform,
                        "disabled": monitor.disabled,
                        "availableModes": monitor.available_modes,
                        "mirrorOf": monitor.mirror_of,
                        "vrr": monitor.vrr,
                        "currentFormat": monitor.current_format,
                    }
                )
            )
        return self._merge_saved_overrides(values)

    @staticmethod
    def _merge_saved_overrides(configs: list[MonitorConfig]) -> list[MonitorConfig]:
        """Recover fields that monitor JSON reports as capabilities, not rules."""
        try:
            contents = MONITORS_PATH.read_text()
        except OSError:
            return configs
        blocks = re.findall(r"hl\.monitor\s*\(\s*\{(.*?)\}\s*\)", contents, re.S)
        overrides: dict[str, tuple[int, int]] = {}
        for block in blocks:
            output = re.search(r'output\s*=\s*"([^"]+)"', block)
            wide = re.search(r"supports_wide_color\s*=\s*(-?\d+)", block)
            hdr = re.search(r"supports_hdr\s*=\s*(-?\d+)", block)
            if output:
                overrides[output[1]] = (
                    int(wide[1]) if wide else 0,
                    int(hdr[1]) if hdr else 0,
                )
        return [
            replace(config, wide_color=overrides[config.name][0], hdr=overrides[config.name][1])
            if config.name in overrides
            else config
            for config in configs
        ]

    def refresh(self) -> None:
        if self._rollback_source:
            self._revert()
        configs = self._query()
        if not configs:
            self._show_error("Hyprland did not report any connected displays.")
            return
        self._configs = configs
        names = [config.name for config in configs]
        self._selected = self._selected if self._selected in names else names[0]
        self._replace_picker(names)
        self._dirty = False
        self._baseline_primary = self._primary_settings.primary_monitor
        self._draft_primary = self._baseline_primary
        self._apply_button.set_sensitive(False)
        self._show_error("")
        self._layout.request_recenter()
        self._render()

    def _replace_picker(self, names: list[str]) -> None:
        self._syncing = True
        model = Gtk.StringList.new(names)
        self._monitor_picker.set_model(model)
        self._monitor_picker.set_selected(names.index(self._selected))
        self._syncing = False

    def _select_from_picker(self, picker, *_args) -> None:
        if self._syncing:
            return
        selected = picker.get_selected_item()
        if selected:
            self._selected = selected.get_string()
            self._render()

    def _config(self, name: str | None = None) -> MonitorConfig:
        target = name or self._selected
        return next(config for config in self._configs if config.name == target)

    def _set(self, **changes) -> None:
        index = next(i for i, config in enumerate(self._configs) if config.name == self._selected)
        self._configs[index] = replace(self._configs[index], **changes)
        if changes.get("hdr") == 1:
            self._configs[index] = replace(
                self._configs[index], wide_color=1, bit_depth=10
            )
        self._mark_dirty()
        self._render()

    def _mark_dirty(self) -> None:
        self._dirty = True
        self._apply_button.set_sensitive(True)
        self._show_error("")

    def _layout_changed(self, name: str, x: int, y: int) -> None:
        self._selected = name
        config = self._config(name)
        if (config.x, config.y) != (x, y):
            index = self._configs.index(config)
            self._configs[index] = replace(config, x=x, y=y)
            self._mark_dirty()
        names = [item.name for item in self._configs]
        self._syncing = True
        self._monitor_picker.set_selected(names.index(name))
        self._syncing = False
        self._render()

    def _row(self, label: str, subtitle: str, control, icon: str) -> Widget.Box:
        Gtk.Widget.set_valign(control, Gtk.Align.CENTER)
        Gtk.Widget.set_vexpand(control, False)
        return Widget.Box(
            spacing=14,
            child=[
                Widget.Icon(
                    image=icon,
                    pixel_size=20,
                    valign="center",
                    css_classes=["settings-row-icon"],
                ),
                Widget.Box(
                    vertical=True,
                    spacing=2,
                    hexpand=True,
                    valign="center",
                    child=[
                        Widget.Label(label=label, halign="start", css_classes=["settings-row-title"]),
                        Widget.Label(
                            label=subtitle, halign="start", wrap=True,
                            visible=bool(subtitle),
                            css_classes=["settings-row-subtitle"],
                        ),
                    ],
                ),
                control,
            ],
            css_classes=["settings-row"],
        )

    @staticmethod
    def _dropdown(values: list[str], current: int, changed: Callable[[int], None]):
        dropdown = Gtk.DropDown.new_from_strings(values)
        dropdown.add_css_class("settings-dropdown")
        dropdown.set_valign(Gtk.Align.CENTER)
        dropdown.set_selected(max(0, min(current, len(values) - 1)))
        dropdown.connect("notify::selected", lambda widget, *_: changed(widget.get_selected()))
        return dropdown

    def _render(self) -> None:
        config = self._config()
        self._layout.update(self._configs, self._selected)
        rows: list[Gtk.Widget] = []

        enable = Widget.Switch(
            active=config.enabled,
            valign="center",
            on_change=lambda _, active: self._set(enabled=active),
        )
        rows.append(self._row("Use this display", config.description, enable, "video-display-symbolic"))

        primary = Widget.Switch(
            active=self._draft_primary == config.name,
            sensitive=config.enabled and not bool(config.mirror),
            valign="center",
            on_change=lambda _, active: self._set_primary(config.name) if active else None,
        )
        rows.append(
            self._row(
                "Primary display",
                "Primary-only shell surfaces and notifications appear here.",
                primary,
                "starred-symbolic",
            )
        )

        try:
            mode_index = config.available_modes.index(config.mode)
        except ValueError:
            mode_index = 0
        mode = self._dropdown(
            config.available_modes,
            mode_index,
            lambda index: self._set(mode=config.available_modes[index]),
        )
        mode.set_sensitive(config.enabled and not bool(config.mirror))
        rows.append(self._row("Resolution and refresh rate", "Select a mode advertised by the display.", mode, "preferences-desktop-display-symbolic"))

        scale_values = list(SCALES)
        if all(abs(config.scale - value) > 0.001 for value in scale_values):
            scale_values.append(config.scale)
            scale_values.sort()
        scale_labels = [f"{value * 100:g}%" for value in scale_values]
        scale = self._dropdown(
            scale_labels,
            min(range(len(scale_values)), key=lambda i: abs(scale_values[i] - config.scale)),
            lambda index: self._set(scale=scale_values[index]),
        )
        scale.set_sensitive(config.enabled and not bool(config.mirror))
        rows.append(self._row("Scale", "Increase the size of text and interface elements.", scale, "zoom-in-symbolic"))

        transform = self._dropdown(
            TRANSFORMS,
            config.transform,
            lambda index: self._set(transform=index),
        )
        transform.set_sensitive(config.enabled and not bool(config.mirror))
        rows.append(self._row("Orientation", "Rotate or flip the display output.", transform, "object-rotate-right-symbolic"))

        x_spin = Gtk.SpinButton.new_with_range(-32768, 32768, 1)
        y_spin = Gtk.SpinButton.new_with_range(-32768, 32768, 1)
        for spin, value, axis in ((x_spin, config.x, "x"), (y_spin, config.y, "y")):
            spin.set_value(value)
            spin.set_width_chars(6)
            spin.set_sensitive(config.enabled and not bool(config.mirror))
            spin.set_valign(Gtk.Align.CENTER)
            spin.connect("value-changed", lambda widget, key=axis: self._set(**{key: widget.get_value_as_int()}))
            spin.add_css_class("settings-display-position")
        rows.append(
            self._row(
                "Position",
                "Exact coordinates in Hyprland’s logical virtual screen.",
                Widget.Box(spacing=8, child=[Widget.Label(label="X"), x_spin, Widget.Label(label="Y"), y_spin]),
                "view-grid-symbolic",
            )
        )

        mirror_targets = ["None"] + [item.name for item in self._configs if item.name != config.name and item.enabled]
        mirror_value = config.mirror if config.mirror in mirror_targets else "None"
        mirror = self._dropdown(
            mirror_targets,
            mirror_targets.index(mirror_value),
            lambda index: self._set(mirror="" if index == 0 else mirror_targets[index]),
        )
        mirror.set_sensitive(config.enabled)
        rows.append(self._row("Mirror", "Show another display’s contents on this output.", mirror, "view-mirror-symbolic"))

        vrr_values = ["Off", "Always", "Fullscreen", "Fullscreen games and video"]
        vrr = self._dropdown(
            vrr_values,
            max(0, min(config.vrr, 3)),
            lambda index: self._set(vrr=index),
        )
        vrr.set_sensitive(config.enabled)
        rows.append(self._row("Variable refresh rate", "Choose when adaptive sync is allowed.", vrr, "view-refresh-symbolic"))

        bit_depth = self._dropdown(
            ["8 bit", "10 bit"],
            1 if config.bit_depth == 10 else 0,
            lambda index: self._set(bit_depth=10 if index else 8, hdr=-1 if not index else config.hdr),
        )
        bit_depth.set_sensitive(config.enabled)
        rows.append(self._row("Colour depth", "10-bit output is required for HDR.", bit_depth, "applications-graphics-symbolic"))

        override_values = ["Off", "Automatic", "On"]
        wide = self._dropdown(
            override_values,
            config.wide_color + 1,
            lambda index: self._set(
                wide_color=index - 1,
                hdr=config.hdr if index else -1,
            ),
        )
        wide.set_sensitive(config.enabled)
        rows.append(self._row("Wide colour gamut", "Use the display’s wider colour space when supported.", wide, "color-select-symbolic"))
        hdr = self._dropdown(
            override_values,
            config.hdr + 1,
            lambda index: self._set(hdr=index - 1),
        )
        hdr.set_sensitive(config.enabled)
        rows.append(self._row("HDR", "Enable high dynamic range output (experimental in Hyprland).", hdr, "display-brightness-symbolic"))

        children: list[Gtk.Widget] = []
        for index, row in enumerate(rows):
            if index:
                children.append(Widget.Separator(css_classes=["settings-row-separator"]))
            children.append(row)
        util.replace_box_children(self._details, children)

    def _set_primary(self, name: str) -> None:
        self._draft_primary = name
        self._mark_dirty()
        self._render()

    def _validate(self) -> str:
        enabled = [config for config in self._configs if config.enabled]
        desktops = [config for config in enabled if not config.mirror]
        if not desktops:
            return "At least one non-mirrored display must remain enabled."
        if self._draft_primary not in [item.name for item in desktops]:
            return "The primary display must be enabled and cannot mirror another display."
        for config in enabled:
            if config.scale < 0.5 or config.scale > 4:
                return f"{config.name} has an unsupported scale."
            mode_width, mode_height, _ = _mode_parts(config.mode)
            if (
                abs(mode_width / config.scale - round(mode_width / config.scale)) > 0.01
                or abs(mode_height / config.scale - round(mode_height / config.scale)) > 0.01
            ):
                return f"{config.name}’s scale does not produce whole logical pixels."
            if config.mirror and config.mirror not in [item.name for item in desktops]:
                return f"{config.name} has an invalid mirror target."
        for index, first in enumerate(desktops):
            fw, fh = first.logical_size
            for second in desktops[index + 1 :]:
                sw, sh = second.logical_size
                overlap = not (
                    first.x + fw <= second.x
                    or second.x + sw <= first.x
                    or first.y + fh <= second.y
                    or second.y + sh <= first.y
                )
                if overlap:
                    return f"{first.name} and {second.name} overlap in the virtual layout."
        return ""

    def _generate(self) -> str:
        lines = [
            "-- Generated by Ignis Settings. Manual changes may be overwritten.",
            "",
        ]
        for config in self._configs:
            lines.extend(["hl.monitor({", f'    output = "{config.name}",'])
            if not config.enabled:
                lines.append("    disabled = true,")
            else:
                lines.extend(
                    [
                        f'    mode = "{config.mode}",',
                        f'    position = "{config.x}x{config.y}",',
                        f"    scale = {config.scale:g},",
                        f"    transform = {config.transform},",
                        f"    vrr = {config.vrr},",
                        f"    bitdepth = {config.bit_depth},",
                        f"    supports_wide_color = {config.wide_color},",
                        f"    supports_hdr = {config.hdr},",
                        f"    sdrbrightness = {config.sdr_brightness:g},",
                    ]
                )
                if config.mirror:
                    lines.append(f'    mirror = "{config.mirror}",')
            lines.extend(["})", ""])
        return "\n".join(lines)

    @staticmethod
    def _write_atomic(path: Path, contents: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(contents)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_path, 0o644)
            os.replace(temp_path, path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _reload_hyprland(self) -> bool:
        try:
            response = str(util.hyprland.send_command("reload"))
            return "error" not in response.lower()
        except Exception:
            return False

    def _restore_snapshot(self) -> None:
        if self._old_file is None:
            if MONITORS_PATH.exists():
                MONITORS_PATH.unlink()
        else:
            self._write_atomic(MONITORS_PATH, self._old_file)
        if self._old_primary:
            self._primary_settings.set_primary_monitor(self._old_primary)
            self._primary_settings.sync()

    def _apply(self) -> None:
        error = self._validate()
        if error:
            self._show_error(error)
            return
        try:
            self._old_file = MONITORS_PATH.read_bytes() if MONITORS_PATH.exists() else None
            self._old_primary = self._baseline_primary
            self._write_atomic(MONITORS_PATH, self._generate().encode())
            self._primary_settings.set_primary_monitor(self._draft_primary)
            self._primary_settings.sync()
            if not self._reload_hyprland():
                raise RuntimeError("Hyprland rejected the configuration reload")
        except Exception as exc:
            try:
                self._restore_snapshot()
                self._reload_hyprland()
            except OSError:
                pass
            self._show_error(f"Could not save display configuration: {exc}")
            return
        self._dirty = False
        self._apply_button.set_sensitive(False)
        self._rollback_seconds = 15
        self._rollback.set_reveal_child(True)
        self._tick_rollback()
        self._rollback_source = GLib.timeout_add_seconds(1, self._tick_rollback)

    def _tick_rollback(self) -> bool:
        if self._rollback_seconds <= 0:
            self._revert()
            return False
        self._rollback_label.set_label(
            f"Keep these display settings? Reverting in {self._rollback_seconds} seconds."
        )
        self._rollback_seconds -= 1
        return True

    def _keep(self) -> None:
        if self._rollback_source:
            GLib.source_remove(self._rollback_source)
            self._rollback_source = 0
        self._old_file = None
        self._baseline_primary = self._draft_primary
        self._rollback.set_reveal_child(False)
        self._schedule_refresh()

    def _revert(self, schedule_refresh: bool = True) -> None:
        if self._rollback_source:
            GLib.source_remove(self._rollback_source)
            self._rollback_source = 0
        try:
            self._restore_snapshot()
            self._reload_hyprland()
        except OSError as exc:
            self._show_error(f"Could not restore the previous display configuration: {exc}")
        self._old_file = None
        self._rollback.set_reveal_child(False)
        if schedule_refresh:
            self._schedule_refresh()

    def _show_error(self, message: str) -> None:
        self._error.set_label(message)
        self._error.set_visible(bool(message))

    def _cleanup(self, *_args) -> None:
        # Closing Settings during confirmation must never silently accept a
        # potentially unusable monitor arrangement.
        if self._rollback_source:
            self._revert(schedule_refresh=False)
        if self._refresh_source:
            GLib.source_remove(self._refresh_source)
            self._refresh_source = 0
        for source, handler in self._signal_handlers:
            try:
                source.disconnect(handler)
            except (TypeError, RuntimeError):
                pass
        self._signal_handlers.clear()


def build_displays_page(SettingsPage, primary_settings):
    return SettingsPage(
        title="Displays",
        description="Arrange displays and configure how Hyprland uses each output.",
        child=[DisplaySettings(primary_settings)],
    )
