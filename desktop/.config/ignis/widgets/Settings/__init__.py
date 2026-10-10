import asyncio
import json
import os
import platform
import shlex
import socket
import uuid
import weakref
from pathlib import Path
from typing import Any, Callable, Literal, cast
from gi.repository import Gdk, GLib, Gtk  # pyright: ignore[reportMissingModuleSource]
from ignis.base_widget import BaseWidget
from ignis.services.bluetooth import BluetoothDevice, BluetoothService
from ignis.services.audio import AudioService, Stream
from ignis.services.network import NetworkService, WifiAccessPoint, WifiDevice
from ignis.services.network._imports import NM
from ignis.widgets import Widget
from util import BindableSettings, JsonSettings
import util
from widgets.Settings.style_settings import style_settings
from widgets.Clock import clock_settings
from widgets.Launcher.currencies import CURRENCY_CODES
from widgets.Launcher.settings import launcher_settings
from widgets.Launcher.app_mode import app_settings
from widgets.Tray import tray_settings
from services.power_profiles.service import (
    power_profiles,
    set_power_profile,
    transform_power_profile_name,
)
from power_settings import power_settings
from keyboard_settings import (
    KeyboardChoice,
    KeyboardLayoutConfig,
    get_keyboard_layouts,
    get_keyboard_variants,
    parse_keyboard_config,
    serialize_keyboard_config,
)
from pointer_settings import (
    POINTER_SPEED_MAPPING_VERSION,
    logical_speed_from_sensitivity,
    migrate_pointer_settings,
    parse_hyprland_pointer_config,
    render_hyprland_pointer_config,
)
from hyprland_options import (
    BASE_KEYS,
    MODIFIER_KEYS,
    LEGACY_OPTIONS_PATH,
    OPTIONS_PATH,
    CustomShortcut,
    Keybind,
    default_keybindings_json,
    keybind_definitions,
    legacy_options,
    parse_custom_shortcuts,
    parse_keybindings,
    render_options,
    serialize_custom_shortcuts,
    serialize_keybindings,
    write_atomic,
)

network_service = NetworkService.get_default()
bluetooth_service = BluetoothService.get_default()
audio_service = AudioService.get_default()

HyprlandLayout = Literal["master"] | Literal["dwindle"]
hyprland_layouts: list[HyprlandLayout] = ["master", "dwindle"]


def _clamp_workspace_count(value: Any) -> int:
    try:
        return max(1, min(10, int(value)))
    except (TypeError, ValueError):
        return 10


def _existing_pointer_defaults() -> tuple[float, bool]:
    try:
        with open(
            os.path.expanduser("~/.local/share/ignis/ignis-hyprland.lua")
        ) as config_file:
            existing = parse_hyprland_pointer_config(config_file.read())
    except OSError:
        existing = parse_hyprland_pointer_config("")

    return (
        logical_speed_from_sensitivity(existing.sensitivity, existing.profile),
        existing.acceleration_enabled,
    )


_default_pointer_sensitivity, _default_acceleration_enabled = (
    _existing_pointer_defaults()
)


@JsonSettings("hyprland")
class HyprlandSettings(BindableSettings):
    keyboard_layout: str = "us"
    keyboard_variant: str = ""

    def set_keyboard_layout(self, value: str) -> None:
        self.keyboard_layout = value

    def set_keyboard_variant(self, value: str) -> None:
        self.keyboard_variant = value

    def get_keyboard_configs(self) -> list[KeyboardLayoutConfig]:
        return parse_keyboard_config(self.keyboard_layout, self.keyboard_variant)

    def set_keyboard_configs(self, entries: list[KeyboardLayoutConfig]) -> None:
        if not entries:
            return
        layouts, variants = serialize_keyboard_config(entries)
        self.set_many(keyboard_layout=layouts, keyboard_variant=variants)

    layout_type: HyprlandLayout = "master"

    def set_layout_type(self, value: HyprlandLayout) -> None:
        self.layout_type = value
        self.schedule_hyprland_reload()

    workspaces_span_displays: bool = False
    workspace_count: int = 10
    hide_empty_workspaces: bool = False

    def set_workspaces_span_displays(self, value: bool) -> None:
        self.workspaces_span_displays = bool(value)
        self.schedule_hyprland_reload()

    def set_workspace_count(self, value: int) -> None:
        count = _clamp_workspace_count(value)
        definitions = keybind_definitions(10, 10)
        bindings = parse_keybindings(self.keybindings_json, definitions)
        self.set_many(
            workspace_count=count,
            keybindings_json=serialize_keybindings(bindings, definitions),
        )
        self.schedule_hyprland_reload()

    def set_hide_empty_workspaces(self, value: bool) -> None:
        self.hide_empty_workspaces = value

    pointer_sensitivity: float = _default_pointer_sensitivity
    acceleration_enabled: bool = _default_acceleration_enabled
    pointer_speed_mapping_version: int = POINTER_SPEED_MAPPING_VERSION

    program_terminal: str = "ghostty"
    program_file_manager: str = "nautilus --new-window"
    program_menu: str = "goignis open-window ignis_launcher_proxy"
    program_browser: str = "helium-browser"
    program_editor: str = "nvim"
    keybindings_json: str = default_keybindings_json()
    custom_shortcuts_json: str = "[]"

    @staticmethod
    def migrate_settings(data: dict[str, Any]) -> dict[str, Any]:
        migrated = migrate_pointer_settings(data)
        for name, value in legacy_options().items():
            migrated.setdefault(name, value)
        workspace_count = _clamp_workspace_count(
            migrated.get("workspace_count", 10)
        )
        old_workspace_mode = migrated.pop("workspace_mode", "primary")
        span_displays = migrated.get(
            "workspaces_span_displays", old_workspace_mode == "all"
        )
        migrated["workspace_count"] = workspace_count
        migrated["workspaces_span_displays"] = bool(span_displays)
        definitions = keybind_definitions(10, 10)
        mod1 = migrated.pop("mod1", "SUPER")
        mod2 = migrated.pop("mod2", "ALT")
        migrated["keybindings_json"] = serialize_keybindings(
            parse_keybindings(
                migrated.get("keybindings_json", ""),
                definitions,
                mod1=mod1,
                mod2=mod2,
            ),
            definitions,
        )
        migrated["custom_shortcuts_json"] = serialize_custom_shortcuts(
            parse_custom_shortcuts(
                migrated.get("custom_shortcuts_json", "[]")
            )
        )
        return migrated

    def set_pointer_sensitivity(self, value: float) -> None:
        self.pointer_sensitivity = value

    def set_acceleration_enabled(self, value: bool) -> None:
        self.acceleration_enabled = value

    def set_program(self, name: str, value: str) -> None:
        setting = f"program_{name}"
        if setting not in {
            "program_terminal",
            "program_file_manager",
            "program_menu",
            "program_browser",
            "program_editor",
        }:
            raise ValueError(f"Unknown program setting: {name}")
        setattr(self, setting, value)
        self.schedule_hyprland_reload()

    def schedule_hyprland_reload(self) -> None:
        source_id = getattr(self, "_hyprland_reload_source_id", None)
        if source_id is not None:
            GLib.source_remove(source_id)

        def reload_hyprland() -> bool:
            self._hyprland_reload_source_id = None
            util.shell("hyprctl reload")
            return False

        self._hyprland_reload_source_id = GLib.timeout_add(
            400, reload_hyprland
        )

    def swap_alt_super(self) -> None:
        definitions = keybind_definitions(10, 10)
        bindings = self.get_keybindings()
        swapped: dict[str, Keybind] = {}
        for action, binding in bindings.items():
            selected = {
                "SUPER" if modifier == "ALT" else
                "ALT" if modifier == "SUPER" else
                modifier
                for modifier in binding.modifiers
            }
            modifiers = tuple(
                modifier
                for modifier in MODIFIER_KEYS
                if modifier in selected
            )
            swapped[action] = Keybind(
                binding.enabled, modifiers, binding.key
            )
        custom_shortcuts = [
            CustomShortcut(
                shortcut.id,
                shortcut.name,
                shortcut.command,
                Keybind(
                    shortcut.binding.enabled,
                    tuple(
                        modifier
                        for modifier in MODIFIER_KEYS
                        if modifier in {
                            "SUPER" if value == "ALT" else
                            "ALT" if value == "SUPER" else value
                            for value in shortcut.binding.modifiers
                        }
                    ),
                    shortcut.binding.key,
                ),
            )
            for shortcut in self.get_custom_shortcuts()
        ]
        self.set_many(
            keybindings_json=serialize_keybindings(swapped, definitions),
            custom_shortcuts_json=serialize_custom_shortcuts(custom_shortcuts),
        )
        self.schedule_hyprland_reload()

    def get_keybind_definitions(self):
        return keybind_definitions(
            (monitor.id + 1 for monitor in util.hyprland.monitors),
            self.workspace_count,
        )

    def get_keybindings(self) -> dict[str, Keybind]:
        return parse_keybindings(
            self.keybindings_json, keybind_definitions(10, 10)
        )

    def set_keybinding(self, action: str, binding: Keybind) -> None:
        bindings = self.get_keybindings()
        if action not in bindings:
            raise ValueError(f"Unknown keybinding: {action}")
        if binding.key not in BASE_KEYS:
            raise ValueError(f"Unknown key symbol: {binding.key}")
        bindings[action] = binding
        self.keybindings_json = serialize_keybindings(
            bindings, keybind_definitions(10, 10)
        )
        self.schedule_hyprland_reload()

    def get_custom_shortcuts(self) -> list[CustomShortcut]:
        return parse_custom_shortcuts(self.custom_shortcuts_json)

    def add_custom_shortcut(self) -> str:
        shortcut_id = uuid.uuid4().hex
        shortcuts = self.get_custom_shortcuts()
        shortcuts.append(
            CustomShortcut(
                id=shortcut_id,
                name="Custom shortcut",
                command="",
                binding=Keybind(False, ("SUPER",), "A"),
            )
        )
        self.custom_shortcuts_json = serialize_custom_shortcuts(shortcuts)
        self.schedule_hyprland_reload()
        return shortcut_id

    def update_custom_shortcut(
        self,
        shortcut_id: str,
        *,
        name: str | None = None,
        command: str | None = None,
        binding: Keybind | None = None,
    ) -> None:
        shortcuts = self.get_custom_shortcuts()
        for index, shortcut in enumerate(shortcuts):
            if shortcut.id == shortcut_id:
                shortcuts[index] = CustomShortcut(
                    id=shortcut.id,
                    name=shortcut.name if name is None else name,
                    command=(
                        shortcut.command if command is None else command
                    ),
                    binding=shortcut.binding if binding is None else binding,
                )
                break
        else:
            raise ValueError(f"Unknown custom shortcut: {shortcut_id}")
        self.custom_shortcuts_json = serialize_custom_shortcuts(shortcuts)
        self.schedule_hyprland_reload()

    def remove_custom_shortcut(self, shortcut_id: str) -> None:
        shortcuts = [
            shortcut
            for shortcut in self.get_custom_shortcuts()
            if shortcut.id != shortcut_id
        ]
        self.custom_shortcuts_json = serialize_custom_shortcuts(shortcuts)
        self.schedule_hyprland_reload()

    def sync(self) -> None:
        pointer_config = render_hyprland_pointer_config(
            self.pointer_sensitivity, self.acceleration_enabled
        ).replace(
            "\n", "\n        "
        )
        with open(
            os.path.expanduser("~/.local/share/ignis/ignis-hyprland.lua"),
            "w",
        ) as f:
            f.write(
f"""-- Ignis generated Hyprland config, do not edit
-- Please put manual changes in ~/.config/hypr/hyprland-custom.lua

hl.config({{
    input = {{
        kb_layout = "{self.keyboard_layout}",
        kb_variant = "{self.keyboard_variant}",

        {pointer_config}
    }},

    general = {{
        layout = "{self.layout_type}",
    }},
}})
"""
            )


        with open(os.path.expanduser("~/.local/share/ignis/hyprlock.conf"), "w") as f:
            f.write(
                f"""
# Ignis generated Hyprlock config, do not edit
$primary_monitor={self.primary_monitor}
"""
            )

        write_atomic(
            Path(os.path.expanduser("~/.local/share/ignis/workspace-state.json")),
            json.dumps(
                {
                    "primary_monitor": self.primary_monitor,
                    "workspaces_span_displays": self.workspaces_span_displays,
                },
                separators=(",", ":"),
            )
            + "\n",
        )
        write_atomic(
            OPTIONS_PATH,
            render_options(
                programs={
                    "terminal": self.program_terminal,
                    "fileManager": self.program_file_manager,
                    "menu": self.program_menu,
                    "browser": self.program_browser,
                    "editor": self.program_editor,
                },
                keybindings=self.get_keybindings(),
                custom_shortcuts=self.get_custom_shortcuts(),
                workspaces_span_displays=self.workspaces_span_displays,
                workspace_count=self.workspace_count,
                primary_monitor=self.primary_monitor,
                layout_type=self.layout_type,
                definitions=self.get_keybind_definitions(),
            ),
        )
        try:
            LEGACY_OPTIONS_PATH.unlink()
        except FileNotFoundError:
            pass

    primary_monitor: str = util.hyprland.monitors[0].name

    def set_primary_monitor(self, value: str) -> None:
        self.primary_monitor = value


hyprland_settings = HyprlandSettings()


class AccentColourButton(Widget.Button):
    def __init__(
        self,
        colour: str,
        wallpaper: str,
        selected: bool,
        on_selected,
        on_removed=None,
    ):
        super().__init__(
            child=(
                Widget.Icon(
                    image="object-select-symbolic",
                    pixel_size=16,
                    css_classes=["settings-suggested-accent-colour-check"],
                )
                if selected
                else None
            ),
            style=f"background-color: {colour};",
            css_classes=[
                "settings-suggested-accent-colour",
                *(["selected"] if selected else []),
            ],
            width_request=32,
            height_request=32,
            valign="center",
            vexpand=False,
            can_target=not selected or on_removed is not None,
            focusable=not selected,
            on_click=lambda _: (
                None if selected else on_selected(colour, wallpaper)
            ),
        )
        self._remove_controller: Gtk.GestureClick | None = None
        if on_removed is not None:
            self._remove_controller = Gtk.GestureClick()
            self._remove_controller.set_button(3)
            self._remove_controller.connect(
                "pressed",
                lambda *_: GLib.idle_add(
                    lambda: (on_removed(colour), False)[1]
                ),
            )
            self.add_controller(self._remove_controller)


class WallpaperButton(Widget.Overlay):
    def __init__(
        self, path: str, on_wallpaper_picked, on_wallpaper_removed, iscurrent: bool
    ):
        wallpaper_size = 196
        super().__init__(
            child=Widget.Button(
                child=Widget.Picture(
                    image=path,
                    content_fit="scale_down",
                    height=wallpaper_size,
                    width=wallpaper_size * 16 // 9,
                    css_classes=["settings-wallpaper-image"],
                ),
                on_click=lambda _: util.create_task(on_wallpaper_picked(path)),
                css_classes=["settings-wallpaper"],
            ),
            overlays=[
                Widget.Box(
                    child=[
                        Widget.Icon(
                            image="object-select-symbolic",
                            pixel_size=16,
                            halign="center",
                            valign="center",
                            hexpand=True,
                            vexpand=True,
                        )
                    ],
                    width_request=32,
                    height_request=32,
                    halign="end",
                    valign="start",
                    hexpand=False,
                    vexpand=False,
                    can_target=False,
                    visible=iscurrent,
                    css_classes=["settings-wallpaper-selected"],
                ),
                Widget.Button(
                    child=Widget.Icon(
                        icon_name="process-stop-symbolic",
                        css_classes=["settings-wallpaper-remove-icon"],
                        pixel_size=12,
                    ),
                    halign="end",
                    valign="start",
                    hexpand=False,
                    vexpand=False,
                    css_classes=["settings-wallpaper-remove-button"],
                    on_click=lambda _: on_wallpaper_removed(path),
                    visible=not iscurrent,
                ),
            ],
            hexpand=False,
            vexpand=True,
            valign="start",
            halign="start",
            css_classes=["settings-wallpaper-overlay"],
        )


class Setting(Widget.Box):
    def __init__(
        self,
        widget: BaseWidget,
        label: str = "",
        subtitle: str = "",
        icon: str | None = None,
        label_hexpand: bool = True,
        sensitive=True,
    ):
        # Some Ignis widgets expose string-based alignment setters. Call GTK's
        # base implementation here so this also works for raw GTK controls.
        Gtk.Widget.set_valign(widget, Gtk.Align.CENTER)
        Gtk.Widget.set_vexpand(widget, False)
        labels = Widget.Box(
            vertical=True,
            spacing=2,
            hexpand=label_hexpand,
            valign="center",
            child=[
                Widget.Label(
                    label=label,
                    css_classes=["settings-row-title"],
                    halign="start",
                    wrap=True,
                ),
                Widget.Label(
                    label=subtitle,
                    css_classes=["settings-row-subtitle"],
                    halign="start",
                    wrap=True,
                    visible=bool(subtitle),
                ),
            ],
        )
        children: list[BaseWidget] = []
        if icon:
            children.append(
                Widget.Icon(
                    image=icon,
                    pixel_size=20,
                    css_classes=["settings-row-icon"],
                    valign="center",
                )
            )
        children.extend([labels, widget])
        super().__init__(
            child=children,
            spacing=14,
            hexpand=True,
            sensitive=sensitive,
            css_classes=["settings-row"],
        )


class SwitchWithLabel(Setting):
    def __init__(
        self,
        label: str,
        subtitle: str = "",
        icon: str | None = None,
        active: bool = True,
        on_change: Callable[[Widget.Switch, bool], Any] = lambda *_: None,
        sensitive=True,
    ):
        switch = Widget.Switch(
            active=active,
            on_change=on_change,
            valign="center",
            sensitive=sensitive,
        )
        super().__init__(
            label=label,
            subtitle=subtitle,
            icon=icon,
            widget=switch,
        )


class SettingsGroup(Widget.Box):
    def __init__(self, title: str, description: str, child: list[BaseWidget | None]):
        rows = [item for item in child if item is not None]
        grouped: list[BaseWidget] = []
        for index, row in enumerate(rows):
            if index:
                grouped.append(
                    Widget.Separator(css_classes=["settings-row-separator"])
                )
            grouped.append(row)

        heading: list[BaseWidget] = [
            Widget.Label(
                label=title,
                css_classes=["settings-group-title"],
                halign="start",
            )
        ]
        if description:
            desc = Widget.Label(
                css_classes=["settings-group-description"],
                halign="start",
                wrap=True,
            )
            desc.set_markup(description)
            heading.append(desc)

        super().__init__(
            vertical=True,
            spacing=8,
            child=[
                *heading,
                Widget.Box(
                    vertical=True,
                    child=grouped,
                    css_classes=["settings-group-card"],
                ),
            ],
            css_classes=["settings-group"],
        )


class SettingsPage(Widget.Box):
    def __init__(
        self,
        title: str,
        description: str,
        child: list[BaseWidget],
    ) -> None:
        super().__init__(
            vertical=True,
            spacing=22,
            child=[
                Widget.Box(
                    vertical=True,
                    spacing=4,
                    child=[
                        Widget.Label(
                            label=title,
                            css_classes=["settings-page-title"],
                            halign="start",
                        ),
                        Widget.Label(
                            label=description,
                            css_classes=["settings-page-description"],
                            halign="start",
                            wrap=True,
                        ),
                    ],
                    css_classes=["settings-page-heading"],
                ),
                *child,
            ],
            css_classes=["settings-page"],
        )


class WifiConnectionRow(Widget.Button):
    """A Wi-Fi row whose contents can be updated without rebuilding GTK widgets."""

    def __init__(self, access_point: WifiAccessPoint) -> None:
        self._access_point = access_point
        self._icon = Widget.Icon(
            image=access_point.icon_name,
            pixel_size=20,
            css_classes=["settings-connection-icon"],
        )
        self._label = Widget.Label(
            label=access_point.ssid or "Hidden network", halign="start"
        )
        security = access_point.security or "Open network"
        self._subtitle = Widget.Label(
            label=security,
            halign="start",
            visible=bool(security),
            css_classes=["settings-connection-subtitle"],
        )
        super().__init__(
            child=Widget.Box(
                spacing=12,
                child=[
                    self._icon,
                    Widget.Box(
                        vertical=True,
                        spacing=2,
                        hexpand=True,
                        child=[self._label, self._subtitle],
                    ),
                    Widget.Icon(image="go-next-symbolic", pixel_size=14),
                ],
            ),
            on_click=self._connect,
            hexpand=True,
            css_classes=["settings-connection-row"],
        )

    def update(self, access_point: WifiAccessPoint) -> None:
        self._access_point = access_point
        self._icon.image = access_point.icon_name
        self._label.label = access_point.ssid or "Hidden network"
        security = access_point.security or "Open network"
        self._subtitle.label = security
        self._subtitle.visible = bool(security)

    def _connect(self, *_args) -> None:
        util.create_task(self._access_point.connect_to_graphical())


def _new_connection_row(
    *, icon: str, label: str, subtitle: str = "", on_click: Callable
) -> Widget.Button:
    """Build a row for low-frequency connection lists such as Bluetooth."""
    return Widget.Button(
        child=Widget.Box(
            spacing=12,
            child=[
                Widget.Icon(
                    image=icon,
                    pixel_size=20,
                    css_classes=["settings-connection-icon"],
                ),
                Widget.Box(
                    vertical=True,
                    spacing=2,
                    hexpand=True,
                    child=[
                        Widget.Label(label=label, halign="start"),
                        Widget.Label(
                            label=subtitle,
                            halign="start",
                            visible=bool(subtitle),
                            css_classes=["settings-connection-subtitle"],
                        ),
                    ],
                ),
                Widget.Icon(image="go-next-symbolic", pixel_size=14),
            ],
        ),
        on_click=on_click,
        hexpand=True,
        css_classes=["settings-connection-row"],
    )


class CompactConnectionScroll(Widget.Scroll):
    """Grow with a short list, then scroll without yielding space to siblings."""

    def __init__(self, child: Widget.Box, *, visible: Any = True) -> None:
        self._connection_list = child
        super().__init__(
            child=child,
            hexpand=True,
            visible=visible,
            propagate_natural_height=True,
            hscrollbar_policy="never",
            vscrollbar_policy="automatic",
        )
        child.connect("notify::child", self._sync_height)
        self._sync_height()

    def _sync_height(self, *_args) -> None:
        count = max(1, len(self._connection_list.child))
        height = min(360, 16 + count * 58)
        # Avoid a transient min/max inversion when the row count changes in
        # either direction; GTK validates each property assignment separately.
        self.max_content_height = -1
        self.min_content_height = height
        self.max_content_height = height


class ConnectionEditorWindow(Widget.RegularWindow):
    def __init__(self, parent: Gtk.Window) -> None:
        self._content = Widget.Box(vertical=True)
        self._actions = Widget.Box(spacing=8)
        self._close_button = Widget.Button(
            label="Close",
            on_click=lambda _: self.set_visible(False),
            css_classes=["settings-secondary-button"],
        )
        super().__init__(
            namespace="ignis_connection_editor",
            title="Connection settings",
            child=Widget.Box(
                vertical=True,
                spacing=10,
                child=[
                    self._content,
                    Widget.Box(
                        child=[
                            self._close_button,
                            Widget.Box(hexpand=True),
                            self._actions,
                        ],
                    ),
                ],
                css_classes=["settings-connection-editor"],
            ),
            transient_for=parent,
            modal=True,
            hide_on_close=True,
            decorated=False,
            resizable=False,
            default_width=520,
        )
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)

    def _on_key_pressed(
        self, _controller: Gtk.EventControllerKey, keyval: int, *_args
    ) -> bool:
        if keyval != Gdk.KEY_Escape:
            return False
        self.set_visible(False)
        return True

    def edit(
        self, title: str, content: BaseWidget, actions: list[BaseWidget]
    ) -> None:
        self.title = title
        util.replace_box_children(self._content, [content])
        util.replace_box_children(self._actions, actions)
        self.set_focus(self._close_button)
        self.present()
        GLib.idle_add(lambda: (self._close_button.grab_focus(), False)[1])


def _close_connection_editor() -> None:
    try:
        window = util.get_app().get_window("ignis_connection_editor")
    except Exception:
        return
    if window is not None:
        window.set_visible(False)


class SavedWifiConnections(Widget.Box):
    """Saved NetworkManager Wi-Fi profiles, including out-of-range networks."""

    def __init__(
        self, open_editor: Callable[[str, BaseWidget, list[BaseWidget]], None]
    ) -> None:
        self._client = getattr(network_service, "_client")
        self._open_editor = open_editor
        super().__init__(
            vertical=True, spacing=6, css_classes=["settings-connection-list"]
        )
        self._client.connect("notify::connections", self._render)
        self._render()

    def _connections(self) -> list[Any]:
        connections = []
        for connection in self._client.get_connections():
            setting = connection.get_setting_connection()
            if setting is not None and setting.get_connection_type() == "802-11-wireless":
                connections.append(connection)
        return sorted(
            connections,
            key=lambda connection: (connection.get_id() or "").casefold(),
        )

    def _access_point(self, connection: Any) -> WifiAccessPoint | None:
        wireless = connection.get_setting_wireless()
        ssid_bytes = wireless.get_ssid() if wireless is not None else None
        ssid = ssid_bytes.get_data().decode(errors="replace") if ssid_bytes else None
        if not ssid:
            return None
        candidates = [
            ap
            for device in network_service.wifi.devices
            for ap in device.access_points
            if ap.ssid == ssid
        ]
        return max(candidates, key=lambda ap: ap.strength, default=None)

    def _render(self, *_args) -> None:
        rows: list[BaseWidget] = []
        for connection in self._connections():
            ap = self._access_point(connection)
            name = connection.get_id() or "Saved network"
            connected = bool(ap and ap.is_connected)
            header = _new_connection_row(
                icon=ap.icon_name if ap is not None else "network-wireless-symbolic",
                label=name,
                subtitle="Connected" if connected else "Saved",
                on_click=lambda _, conn=connection, point=ap, title=name: self._edit(
                    title, conn, point
                ),
            )
            rows.append(header)

        util.replace_box_children(
            self,
            rows
            or [
                Widget.Label(
                    label="No saved Wi-Fi networks",
                    css_classes=["settings-connection-empty"],
                )
            ],
        )

    def _edit(
        self, title: str, connection: Any, ap: WifiAccessPoint | None
    ) -> None:
        content, actions = self._details(connection, ap)
        self._open_editor(title, content, actions)

    def _details(
        self, connection: Any, ap: WifiAccessPoint | None
    ) -> tuple[BaseWidget, list[BaseWidget]]:
        setting = connection.get_setting_connection()
        security_setting = connection.get_setting_wireless_security()
        password = ""
        if security_setting is not None:
            try:
                secrets = connection.get_secrets("802-11-wireless-security").unpack()
                password = secrets.get("802-11-wireless-security", {}).get("psk", "")
            except GLib.Error:
                pass
        connected = bool(ap and ap.is_connected)
        pending: dict[str, Any] = {
            "name": connection.get_id() or "",
            "autoconnect": bool(setting.get_autoconnect()),
            "password": password,
            "password_changed": False,
        }
        fields: list[BaseWidget] = [
            Setting(
                label="Connection name",
                subtitle="Saved when you press Save.",
                icon="document-edit-symbolic",
                widget=Widget.Entry(
                    text=pending["name"],
                    hexpand=True,
                    on_change=lambda entry: pending.__setitem__("name", entry.text),
                    css_classes=["settings-connection-entry"],
                ),
            ),
            SwitchWithLabel(
                label="Connect automatically",
                icon="network-wireless-symbolic",
                active=pending["autoconnect"],
                on_change=lambda _, active: pending.__setitem__(
                    "autoconnect", active
                ),
            ),
        ]
        if security_setting is not None:
            def password_changed(entry: Widget.Entry) -> None:
                pending["password"] = entry.text
                pending["password_changed"] = True

            fields.append(
                Setting(
                    label="Wi-Fi password",
                    subtitle="Leave unchanged to keep the current password.",
                    icon="dialog-password-symbolic",
                    widget=Widget.Entry(
                        text=password,
                        visibility=False,
                        hexpand=True,
                        on_change=password_changed,
                        css_classes=["settings-connection-entry"],
                    ),
                )
            )
        return Widget.Box(
            vertical=True,
            spacing=8,
            child=fields,
        ), [
            Widget.Button(
                label="Save",
                on_click=lambda _: util.create_task(self._save(connection, pending)),
                css_classes=["settings-secondary-button"],
            ),
            Widget.Button(
                label="Disconnect" if connected else "Connect",
                sensitive=ap is not None,
                on_click=lambda _: self._toggle_connection(ap),
                css_classes=["settings-secondary-button"],
            ),
            Widget.Button(
                label="Forget",
                on_click=lambda _: self._forget(connection),
                css_classes=["settings-destructive-button"],
            ),
        ]

    @staticmethod
    def _toggle_connection(ap: WifiAccessPoint | None) -> None:
        if ap is not None:
            util.create_task(
                ap.disconnect_from() if ap.is_connected else ap.connect_to_graphical()
            )
        _close_connection_editor()

    @staticmethod
    def _forget(connection: Any) -> None:
        util.create_task(connection.delete_async())
        _close_connection_editor()

    async def _save(self, connection: Any, pending: dict[str, Any]) -> None:
        name = str(pending["name"]).strip()
        if not name:
            return
        setting = connection.get_setting_connection()
        setting.set_property("id", name)
        setting.set_property("autoconnect", bool(pending["autoconnect"]))
        security_setting = connection.get_setting_wireless_security()
        if security_setting is not None and pending["password_changed"]:
            security_setting.set_property("psk", pending["password"])
            security_setting.set_secret_flags("psk", NM.SettingSecretFlags.NONE)
        await connection.commit_changes_async(True)
        _close_connection_editor()


class SavedBluetoothConnections(Widget.Box):
    def __init__(
        self, open_editor: Callable[[str, BaseWidget, list[BaseWidget]], None]
    ) -> None:
        self._open_editor = open_editor
        self._device_handlers: list[tuple[BluetoothDevice, int]] = []
        super().__init__(
            vertical=True, spacing=6, css_classes=["settings-connection-list"]
        )
        bluetooth_service.connect("notify::devices", self._render)
        bluetooth_service.connect("notify::powered", self._render)
        self._render()

    def _disconnect_devices(self) -> None:
        for device, handler in self._device_handlers:
            if device.handler_is_connected(handler):
                device.disconnect(handler)
        self._device_handlers.clear()

    def _render(self, *_args) -> None:
        self._disconnect_devices()
        for device in bluetooth_service.devices:
            for prop in ("paired", "connected", "alias", "name", "icon-name"):
                self._device_handlers.append(
                    (device, device.connect(f"notify::{prop}", self._render))
                )
        devices = sorted(
            (device for device in bluetooth_service.devices if device.paired),
            key=lambda device: (device.alias or device.name).casefold(),
        )
        rows: list[BaseWidget] = []
        for device in devices:
            title = device.alias or device.name
            header = _new_connection_row(
                icon=device.icon_name,
                label=title,
                subtitle="Connected" if device.connected else "Paired",
                on_click=lambda _, bluetooth_device=device, name=title: self._edit(
                    name, bluetooth_device
                ),
            )
            rows.append(header)

        util.replace_box_children(
            self,
            rows
            or [
                Widget.Label(
                    label="No paired Bluetooth devices",
                    css_classes=["settings-connection-empty"],
                )
            ],
        )

    def _edit(self, title: str, device: BluetoothDevice) -> None:
        content, actions = self._details(device)
        self._open_editor(title, content, actions)

    def _details(
        self, device: BluetoothDevice
    ) -> tuple[BaseWidget, list[BaseWidget]]:
        pending: dict[str, Any] = {
            "alias": device.alias or device.name,
            "trusted": device.trusted,
        }
        return Widget.Box(
            vertical=True,
            spacing=8,
            child=[
                Setting(
                    label="Device name",
                    subtitle="Saved when you press Save.",
                    icon="document-edit-symbolic",
                    widget=Widget.Entry(
                        text=pending["alias"],
                        hexpand=True,
                        on_change=lambda entry: pending.__setitem__(
                            "alias", entry.text
                        ),
                        css_classes=["settings-connection-entry"],
                    ),
                ),
                SwitchWithLabel(
                    label="Trusted device",
                    subtitle="Allow this device to reconnect without confirmation.",
                    icon="security-high-symbolic",
                    active=pending["trusted"],
                    on_change=lambda _, active: pending.__setitem__(
                        "trusted", active
                    ),
                ),
            ],
        ), [
            Widget.Button(
                label="Save",
                on_click=lambda _: self._save(device, pending),
                css_classes=["settings-secondary-button"],
            ),
            Widget.Button(
                label="Disconnect" if device.connected else "Connect",
                sensitive=bluetooth_service.powered and device.connectable,
                on_click=lambda _: self._toggle_connection(device),
                css_classes=["settings-secondary-button"],
            ),
            Widget.Button(
                label="Forget",
                on_click=lambda _: self._forget(device),
                css_classes=["settings-destructive-button"],
            ),
        ]

    @staticmethod
    def _toggle_connection(device: BluetoothDevice) -> None:
        # connect_service(False) disconnects the profile only; it does not
        # remove the BlueZ device or alter its paired property.
        util.create_task(
            device.disconnect_from() if device.connected else device.connect_to()
        )
        _close_connection_editor()

    @staticmethod
    def _forget(device: BluetoothDevice) -> None:
        util.shell(f"bluetoothctl remove {shlex.quote(device.address)}")
        _close_connection_editor()

    @staticmethod
    def _save(device: BluetoothDevice, pending: dict[str, Any]) -> None:
        alias = str(pending["alias"]).strip()
        if not alias:
            return
        device.gdevice.props.alias = alias
        device.gdevice.props.trusted = bool(pending["trusted"])
        _close_connection_editor()


class NewWifiConnections(Widget.Box):
    def __init__(self) -> None:
        self._device: WifiDevice | None = None
        self._device_handler: int | None = None
        self._ap_handlers: list[tuple[WifiAccessPoint, int]] = []
        self._rows: dict[str, WifiConnectionRow] = {}
        self._status_label = Widget.Label(css_classes=["settings-connection-empty"])
        super().__init__(
            vertical=True,
            spacing=6,
            css_classes=["settings-connection-list"],
        )
        network_service.wifi.connect("notify::devices", self._sync_device)
        network_service.wifi.connect("notify::enabled", self._render)
        self._sync_device()

    @staticmethod
    def _is_saved(ap: WifiAccessPoint) -> bool:
        return bool(getattr(ap, "_connections", ()))

    def _disconnect_access_points(self) -> None:
        for ap, handler in self._ap_handlers:
            if ap.handler_is_connected(handler):
                ap.disconnect(handler)
        self._ap_handlers.clear()

    def _sync_device(self, *_args) -> None:
        if (
            self._device is not None
            and self._device_handler is not None
            and self._device.handler_is_connected(self._device_handler)
        ):
            self._device.disconnect(self._device_handler)
        devices = network_service.wifi.devices
        self._device = devices[0] if devices else None
        self._device_handler = (
            self._device.connect("notify::access-points", self._render)
            if self._device is not None
            else None
        )
        self._render()

    def scan(self) -> None:
        if self._device is not None:
            util.create_task(self._device.scan())

    def _render(self, *_args) -> None:
        self._disconnect_access_points()
        if not network_service.wifi.enabled:
            self._rows.clear()
            self._status_label.label = "Wi-Fi is turned off"
            self._replace_children_if_changed([self._status_label])
            return

        grouped: dict[str, list[WifiAccessPoint]] = {}
        for ap in self._device.access_points if self._device is not None else []:
            if ap.ssid and not self._is_saved(ap):
                grouped.setdefault(ap.ssid, []).append(ap)
        access_points = sorted(
            (max(group, key=lambda ap: ap.strength) for group in grouped.values()),
            key=lambda ap: ap.strength,
            reverse=True,
        )
        previous_rows = self._rows
        current_rows: dict[str, WifiConnectionRow] = {}
        rows: list[BaseWidget] = []
        for ap in access_points:
            # Reuse the row for this SSID. Signal strength changes frequently;
            # updating its contents in place avoids constructing thousands
            # of short-lived GTK widget trees while the settings window is idle.
            key = ap.ssid or ""
            row = previous_rows.get(key)
            if row is None:
                row = WifiConnectionRow(ap)
            else:
                row.update(ap)
            current_rows[key] = row
            rows.append(row)

            for prop in ("strength", "icon-name"):
                self._ap_handlers.append(
                    (ap, ap.connect(f"notify::{prop}", self._update_row, row))
                )
            for prop in ("ssid", "psk"):
                self._ap_handlers.append(
                    (ap, ap.connect(f"notify::{prop}", self._render))
                )

        self._rows = current_rows
        if not rows:
            self._status_label.label = "No new networks found"
            rows = [self._status_label]
        self._replace_children_if_changed(rows)

    def _update_row(
        self, access_point: WifiAccessPoint, _param: object, row: WifiConnectionRow
    ) -> None:
        row.update(access_point)

    def _replace_children_if_changed(self, children: list[BaseWidget]) -> None:
        if list(self.child) != children:
            util.replace_box_children(self, children)


class NewBluetoothConnections(Widget.Box):
    def __init__(self) -> None:
        self._device_handlers: list[tuple[BluetoothDevice, int]] = []
        super().__init__(
            vertical=True,
            spacing=6,
            visible=bluetooth_service.bind("setup_mode"),
            css_classes=["settings-connection-list"],
        )
        bluetooth_service.connect("notify::devices", self._render)
        bluetooth_service.connect("notify::powered", self._render)
        bluetooth_service.connect("notify::setup-mode", self._render)
        self._render()

    def _disconnect_devices(self) -> None:
        for device, handler in self._device_handlers:
            if device.handler_is_connected(handler):
                device.disconnect(handler)
        self._device_handlers.clear()

    def _render(self, *_args) -> None:
        self._disconnect_devices()
        if not bluetooth_service.setup_mode:
            util.replace_box_children(self, [])
            return

        if not bluetooth_service.powered:
            util.replace_box_children(
                self,
                [Widget.Label(label="Bluetooth is turned off", css_classes=["settings-connection-empty"])],
            )
            return

        all_devices = bluetooth_service.devices
        for device in all_devices:
            for prop in ("paired", "connected", "alias", "name", "icon-name"):
                self._device_handlers.append(
                    (device, device.connect(f"notify::{prop}", self._render))
                )

        devices = sorted(
            (device for device in all_devices if not device.paired and device.connectable),
            key=lambda device: (device.alias or device.name).casefold(),
        )
        rows: list[BaseWidget] = []
        for device in devices:
            rows.append(
                _new_connection_row(
                    icon=device.icon_name,
                    label=device.alias or device.name,
                    on_click=lambda _, bluetooth_device=device: util.create_task(
                        bluetooth_device.connect_to()
                    ),
                )
            )
        util.replace_box_children(
            self,
            rows
            or [
                Widget.Label(
                    label="No unpaired devices found",
                    css_classes=["settings-connection-empty"],
                )
            ],
        )


class AirplaneModeSetting(Setting):
    def __init__(self) -> None:
        self._wifi_was_enabled = False
        self._bluetooth_was_powered = False
        self._switch = Widget.Switch(
            active=False,
            on_change=self._changed,
            valign="center",
        )
        super().__init__(
            label="Airplane mode",
            subtitle="Turn off Wi-Fi and Bluetooth radios.",
            icon="airplane-mode-symbolic",
            widget=self._switch,
        )

    def _changed(self, _switch: Widget.Switch, active: bool) -> None:
        if active:
            self._wifi_was_enabled = network_service.wifi.enabled
            self._bluetooth_was_powered = bluetooth_service.powered
            if self._wifi_was_enabled:
                network_service.wifi.set_enabled(False)
            if self._bluetooth_was_powered:
                bluetooth_service.set_powered(False)
            return
        if self._wifi_was_enabled:
            network_service.wifi.set_enabled(True)
        if self._bluetooth_was_powered:
            bluetooth_service.set_powered(True)


class AudioStreamRow(Widget.Box):
    def __init__(self, stream: Stream) -> None:
        label = stream.description or stream.name or "Audio stream"
        mute_icon = stream.bind(
            "is-muted",
            lambda muted: (
                "audio-volume-muted-symbolic"
                if muted
                else "audio-volume-high-symbolic"
            ),
        )
        scale = Widget.Scale(
            min=0,
            max=150,
            step=1,
            value=stream.bind("volume"),
            on_change=lambda scale: stream.set_volume(scale.value),
            draw_value=True,
            value_pos="right",
            width_request=230,
            css_classes=["settings-audio-native-volume"],
        )
        scale.set_format_value_func(lambda _scale, value: f"{round(value)}%")
        scale.add_mark(100, Gtk.PositionType.BOTTOM, None)
        mute = Widget.ToggleButton(
            child=Widget.Icon(
                image=mute_icon,
                pixel_size=18,
            ),
            active=stream.bind("is_muted"),
            on_toggled=lambda _, active: stream.set_is_muted(active),
            valign="center",
            tooltip_text="Unmute" if stream.is_muted else "Mute",
            css_classes=["settings-audio-mute-button"],
        )

        super().__init__(
            spacing=12,
            css_classes=["settings-audio-stream"],
            child=[
                Widget.Icon(
                    image=(
                        stream.icon_name
                        if stream.icon_name != "image-missing"
                        else "audio-x-generic-symbolic"
                    ),
                    pixel_size=20,
                    css_classes=["settings-audio-stream-icon"],
                ),
                Widget.Label(
                    label=label,
                    halign="start",
                    hexpand=True,
                    ellipsize="end",
                ),
                Widget.Box(spacing=4, child=[scale, mute]),
            ],
        )


class AudioDeviceList(Widget.Box):
    def __init__(
        self,
        kind: Literal["speaker", "microphone"],
        open_editor: Callable[[str, BaseWidget, list[BaseWidget]], None],
    ) -> None:
        self._kind = kind
        self._open_editor = open_editor
        self._handlers: list[tuple[Stream, int]] = []
        super().__init__(
            vertical=True,
            spacing=6,
            css_classes=["settings-audio-device-list"],
        )
        audio_service.connect(f"notify::{kind}s", self._render)
        self._render()

    def _render(self, *_args) -> None:
        for stream, handler in self._handlers:
            if stream.handler_is_connected(handler):
                stream.disconnect(handler)
        self._handlers.clear()
        streams: list[Stream] = getattr(audio_service, f"{self._kind}s")
        rows: list[BaseWidget] = []
        for stream in sorted(
            streams,
            key=lambda item: (item.description or item.name or "").casefold(),
        ):
            self._handlers.append(
                (stream, stream.connect("notify::is-default", self._render))
            )
            rows.append(
                Widget.Box(
                    child=[
                        Widget.Button(
                            child=Widget.Box(
                                spacing=10,
                                child=[
                                    Widget.Icon(
                                        image=(
                                            "object-select-symbolic"
                                            if stream.is_default
                                            else "audio-card-symbolic"
                                        ),
                                        css_classes=["settings-audio-device-icon"],
                                    ),
                                    Widget.Label(
                                        label=stream.description or stream.name,
                                        halign="start",
                                        hexpand=True,
                                        ellipsize="end",
                                    ),
                                ],
                            ),
                            hexpand=True,
                            on_click=lambda _, selected=stream: setattr(
                                audio_service, self._kind, selected
                            ),
                            css_classes=["settings-audio-device-select"],
                        ),
                        Widget.Button(
                            label="Modify",
                            on_click=lambda _, selected=stream: self._edit(selected),
                            valign="center",
                            css_classes=["settings-audio-device-modify"],
                        ),
                    ],
                    css_classes=["settings-audio-device-row"],
                )
            )
        util.replace_box_children(
            self,
            rows
            or [
                Widget.Label(
                    label=f"No {self._kind}s found",
                    css_classes=["settings-connection-empty"],
                )
            ],
        )

    def _edit(self, stream: Stream) -> None:
        volume_scale = Widget.Scale(
            min=0,
            max=150,
            step=1,
            value=stream.bind("volume"),
            on_change=lambda scale: stream.set_volume(scale.value),
            draw_value=True,
            value_pos="right",
            width_request=320,
            css_classes=["settings-audio-native-volume"],
        )
        volume_scale.set_format_value_func(
            lambda _scale, value: f"{round(value)}%"
        )
        volume_scale.add_mark(100, Gtk.PositionType.BOTTOM, None)
        volume_row = Setting(
            label="Volume",
            icon=stream.bind("icon-name"),
            widget=Widget.Box(
                spacing=4,
                child=[
                    volume_scale,
                    Widget.ToggleButton(
                        child=Widget.Icon(
                            image=stream.bind("icon-name"), pixel_size=18
                        ),
                        active=stream.bind("is_muted"),
                        on_toggled=lambda _, active: stream.set_is_muted(active),
                        valign="center",
                        vexpand=False,
                        css_classes=["settings-audio-mute-button"],
                    ),
                ],
            ),
        )

        label = "Use as output" if self._kind == "speaker" else "Use as input"
        self._open_editor(
            stream.description or stream.name or "Audio device",
            Widget.Box(
                vertical=True,
                child=[volume_row],
                css_classes=["settings-audio-device-editor"],
            ),
            [
                Widget.Button(
                    label=label,
                    on_click=lambda _: (
                        setattr(audio_service, self._kind, stream),
                        _close_connection_editor(),
                    ),
                    css_classes=["settings-primary-button"],
                )
            ],
        )

class ApplicationVolumeList(Widget.Box):
    def __init__(self) -> None:
        super().__init__(
            vertical=True,
            spacing=6,
            css_classes=["settings-audio-application-list"],
        )
        audio_service.connect("notify::apps", self._render)
        self._render()

    def _render(self, *_args) -> None:
        rows = [AudioStreamRow(stream) for stream in audio_service.apps]
        util.replace_box_children(
            self,
            rows
            or [
                Widget.Label(
                    label="No applications are currently playing audio",
                    css_classes=["settings-connection-empty"],
                )
            ],
        )


def _system_information() -> list[tuple[str, str, str]]:
    os_name = "Linux"
    try:
        values = {}
        with open("/etc/os-release", encoding="utf-8") as release:
            for line in release:
                key, _, value = line.rstrip().partition("=")
                values[key] = value.strip('"')
        os_name = values.get("PRETTY_NAME", os_name)
    except OSError:
        pass

    cpu = platform.processor() or "Unknown"
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as cpuinfo:
            for line in cpuinfo:
                if line.lower().startswith("model name"):
                    cpu = line.partition(":")[2].strip()
                    break
    except OSError:
        pass

    memory = "Unknown"
    try:
        with open("/proc/meminfo", encoding="utf-8") as meminfo:
            total_kib = int(meminfo.readline().split()[1])
            memory = f"{total_kib / 1024 / 1024:.1f} GiB"
    except (OSError, ValueError, IndexError):
        pass

    return [
        ("Operating system", os_name, "computer-symbolic"),
        ("Hostname", socket.gethostname(), "network-server-symbolic"),
        ("Kernel", platform.release(), "utilities-terminal-symbolic"),
        ("Processor", cpu, "xsi-cpu-symbolic"),
        ("Memory", memory, "xsi-ram-symbolic"),
    ]


def StringDropdown(
    *,
    labels: list[str],
    on_change: Callable,
    get_current: Callable | None = None,
    settings_obj=None,
    notify_props: list[str] | None = None,
    enable_search: bool = False,
    choices: list[KeyboardChoice] | None = None,
    repopulate: Callable[[], list[KeyboardChoice]] | None = None,
):
    model = Gtk.StringList()
    syncing = False
    current_values: list[str] = []

    def fill(items: list[KeyboardChoice]):
        nonlocal current_values
        while model.get_n_items():
            model.remove(0)
        current_values = [item.value for item in items]
        for item in items:
            model.append(item.label)

    fill(
        choices
        or [KeyboardChoice(value=label, label=label) for label in labels]
    )

    dropdown = Gtk.DropDown(
        model=model,
        expression=Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"),
    )
    dropdown.set_hexpand(False)
    dropdown.set_halign(Gtk.Align.START)
    dropdown.set_valign(Gtk.Align.CENTER)
    dropdown.add_css_class("settings-dropdown")
    dropdown.set_enable_search(enable_search)

    def on_selected(dd, _):
        nonlocal syncing
        if syncing:
            return
        selected = dd.get_selected()
        if selected < len(current_values):
            on_change(current_values[selected])

    dropdown.connect("notify::selected-item", on_selected)

    def sync_from_settings(*_):
        nonlocal syncing
        if not get_current:
            return
        syncing = True

        if repopulate:
            fill(repopulate())

        try:
            dropdown.set_selected(current_values.index(get_current()))
        except ValueError:
            dropdown.set_selected(0)

        syncing = False

    GLib.idle_add(lambda: (sync_from_settings(), False)[1])

    if settings_obj and notify_props:
        for prop in notify_props:
            settings_obj.connect(f"notify::{prop}", sync_from_settings)

    return cast(BaseWidget, dropdown)


class KeyboardLayoutsEditor(Widget.Box):
    def __init__(self) -> None:
        self._updating = False
        super().__init__(
            vertical=True,
            spacing=6,
            hexpand=True,
            css_classes=["settings-keyboard-layout-list"],
        )
        hyprland_settings.connect("notify::keyboard-layout", self._settings_changed)
        hyprland_settings.connect("notify::keyboard-variant", self._settings_changed)
        self._render()

    def _settings_changed(self, *_args) -> None:
        if not self._updating:
            self._render()

    def _commit(self, entries: list[KeyboardLayoutConfig]) -> None:
        self._updating = True
        try:
            hyprland_settings.set_keyboard_configs(entries)
        finally:
            self._updating = False
        self._render()

    def _set_layout(self, index: int, layout: str) -> None:
        entries = hyprland_settings.get_keyboard_configs()
        entries[index] = KeyboardLayoutConfig(layout=layout)
        self._commit(entries)

    def _set_variant(self, index: int, variant: str) -> None:
        entries = hyprland_settings.get_keyboard_configs()
        entries[index] = KeyboardLayoutConfig(
            layout=entries[index].layout,
            variant=variant,
        )
        self._commit(entries)

    def _remove(self, index: int) -> None:
        entries = hyprland_settings.get_keyboard_configs()
        if len(entries) > 1:
            entries.pop(index)
            self._commit(entries)

    def add(self) -> None:
        entries = hyprland_settings.get_keyboard_configs()
        available = get_keyboard_layouts()
        choice = next(
            (
                item
                for item in sorted(available, key=lambda item: item.value != "us")
            ),
            None,
        )
        if choice is not None:
            self._commit([*entries, KeyboardLayoutConfig(layout=choice.value)])

    def _render(self) -> None:
        entries = hyprland_settings.get_keyboard_configs()
        all_layouts = get_keyboard_layouts()
        rows: list[BaseWidget] = []
        for index, entry in enumerate(entries):
            layout = StringDropdown(
                labels=[],
                choices=all_layouts,
                enable_search=True,
                on_change=lambda value, row=index: self._set_layout(row, value),
                get_current=lambda item=entry: item.layout,
            )
            variant = StringDropdown(
                labels=[],
                choices=get_keyboard_variants(entry.layout),
                enable_search=True,
                on_change=lambda value, row=index: self._set_variant(row, value),
                get_current=lambda item=entry: item.variant,
            )
            remove = Widget.Button(
                child=Widget.Icon(image="edit-delete-symbolic", pixel_size=16),
                tooltip_text="Remove layout",
                css_classes=["settings-keyboard-layout-remove"],
                sensitive=len(entries) > 1,
                valign="center",
                vexpand=False,
                on_click=lambda *_args, row=index: self._remove(row),
            )
            rows.append(
                Widget.Box(
                    spacing=8,
                    child=[layout, variant, Widget.Box(hexpand=True), remove],
                    css_classes=["settings-keyboard-layout-row"],
                )
            )
        util.replace_box_children(self, rows)


class KeybindingEditor(Widget.Box):
    """Compact editor for one GUI-managed Hyprland binding."""

    _instances = weakref.WeakSet()

    def __init__(
        self,
        action: str | None = None,
        *,
        get_binding: Callable[[], Keybind] | None = None,
        on_update: Callable[[Keybind], None] | None = None,
    ) -> None:
        if action is not None:
            get_binding = lambda: hyprland_settings.get_keybindings()[action]
            on_update = lambda binding: hyprland_settings.set_keybinding(
                action, binding
            )
        if get_binding is None or on_update is None:
            raise ValueError("A keybinding action or callbacks are required")
        self._get_binding = get_binding
        self._on_update = on_update
        self._syncing_modifiers = False
        binding = self._get_binding()
        self._modifier_buttons = [
            Widget.ToggleButton(
                label=modifier.title(),
                active=modifier in binding.modifiers,
                on_toggled=lambda _, active, value=modifier: self._set_modifier(
                    value, active
                ),
                css_classes=["settings-keybind-modifier"],
            )
            for modifier in MODIFIER_KEYS
        ]
        self._key = StringDropdown(
            labels=list(BASE_KEYS),
            enable_search=True,
            on_change=self._set_key,
            get_current=lambda: self._get_binding().key,
        )
        self._key.add_css_class("settings-keybind-key")
        self._controls = Widget.Box(
            spacing=6,
            child=[*self._modifier_buttons, self._key],
            sensitive=binding.enabled,
        )
        self._enabled_icon = Widget.Icon(pixel_size=16)
        self._enabled = Widget.ToggleButton(
            child=self._enabled_icon,
            active=binding.enabled,
            on_toggled=self._set_enabled,
            valign="center",
            css_classes=["settings-keybind-enabled"],
        )
        self._sync_enabled_visual(binding.enabled)
        super().__init__(
            spacing=6,
            child=[
                Widget.Box(hexpand=True),
                self._enabled,
                self._controls,
            ],
            hexpand=True,
            css_classes=["settings-keybind-editor"],
        )
        self._instances.add(self)

    @classmethod
    def sync_all_modifiers(cls) -> None:
        for editor in list(cls._instances):
            editor._sync_modifiers()

    def _sync_modifiers(self) -> None:
        selected = self._get_binding().modifiers
        self._syncing_modifiers = True
        try:
            for modifier, button in zip(
                MODIFIER_KEYS, self._modifier_buttons
            ):
                button.active = modifier in selected
        finally:
            self._syncing_modifiers = False

    def _update(self, **changes: Any) -> None:
        current = self._get_binding()
        self._on_update(
            Keybind(
                enabled=changes.get("enabled", current.enabled),
                modifiers=changes.get("modifiers", current.modifiers),
                key=changes.get("key", current.key),
            ),
        )

    def _sync_enabled_visual(self, active: bool) -> None:
        self._enabled_icon.image = (
            "object-select-symbolic" if active else "process-stop-symbolic"
        )
        self._enabled.tooltip_text = (
            "Disable shortcut" if active else "Enable shortcut"
        )

    def _set_enabled(self, _button, active: bool) -> None:
        self._sync_enabled_visual(active)
        self._controls.sensitive = active
        self._update(enabled=active)

    def _set_modifier(self, modifier: str, active: bool) -> None:
        if self._syncing_modifiers:
            return
        current = self._get_binding()
        values = [value for value in current.modifiers if value != modifier]
        if active:
            values.append(modifier)
        self._update(
            modifiers=tuple(value for value in MODIFIER_KEYS if value in values)
        )

    def _set_key(self, value: str) -> None:
        self._update(key=value.strip())


class CustomShortcutRow(Widget.Box):
    def __init__(self, shortcut_id: str, on_remove: Callable[[], None]) -> None:
        self._shortcut_id = shortcut_id
        shortcut = self._get_shortcut()
        name = Widget.Entry(
            text=shortcut.name,
            hexpand=False,
            width_chars=22,
            max_width_chars=30,
            on_change=lambda entry: hyprland_settings.update_custom_shortcut(
                self._shortcut_id, name=entry.text
            ),
        )
        command = Widget.Entry(
            text=shortcut.command,
            hexpand=True,
            on_change=lambda entry: hyprland_settings.update_custom_shortcut(
                self._shortcut_id, command=entry.text
            ),
            css_classes=["settings-custom-shortcut-command"],
        )
        name.set_placeholder_text("Shortcut name")
        command.set_placeholder_text("Shell command")
        remove = Widget.Button(
            child=Widget.Icon(image="edit-delete-symbolic", pixel_size=16),
            tooltip_text="Remove shortcut",
            css_classes=["settings-destructive-button"],
            valign="end",
            on_click=lambda *_: on_remove(),
        )
        fields = Widget.Box(
            spacing=10,
            child=[
                Widget.Box(
                    vertical=True,
                    spacing=4,
                    child=[
                        Widget.Label(
                            label="Name",
                            halign="start",
                            css_classes=["settings-custom-shortcut-field-label"],
                        ),
                        name,
                    ],
                ),
                Widget.Box(
                    vertical=True,
                    spacing=4,
                    hexpand=True,
                    child=[
                        Widget.Label(
                            label="Command",
                            halign="start",
                            css_classes=["settings-custom-shortcut-field-label"],
                        ),
                        command,
                    ],
                ),
                remove,
            ],
        )
        binding = KeybindingEditor(
            get_binding=lambda: self._get_shortcut().binding,
            on_update=lambda value: hyprland_settings.update_custom_shortcut(
                self._shortcut_id, binding=value
            ),
        )
        super().__init__(
            vertical=True,
            spacing=10,
            child=[fields, binding],
            css_classes=["settings-custom-shortcut-row"],
        )

    def _get_shortcut(self) -> CustomShortcut:
        for shortcut in hyprland_settings.get_custom_shortcuts():
            if shortcut.id == self._shortcut_id:
                return shortcut
        raise ValueError(f"Unknown custom shortcut: {self._shortcut_id}")


class CustomShortcutsEditor(Widget.Box):
    def __init__(self) -> None:
        self._rows = Widget.Box(vertical=True)
        add = Widget.Button(
            child=Widget.Box(
                spacing=7,
                child=[
                    Widget.Icon(image="list-add-symbolic", pixel_size=16),
                    Widget.Label(label="Add shortcut"),
                ],
            ),
            halign="start",
            css_classes=[
                "settings-secondary-button",
                "settings-custom-shortcut-add",
            ],
            on_click=lambda *_: self._add(),
        )
        super().__init__(
            vertical=True,
            spacing=12,
            child=[self._rows, add],
            css_classes=["settings-custom-shortcuts-editor"],
        )
        self._render()

    def _add(self) -> None:
        hyprland_settings.add_custom_shortcut()
        self._render()

    def _remove(self, shortcut_id: str) -> None:
        hyprland_settings.remove_custom_shortcut(shortcut_id)
        self._render()

    def _render(self) -> None:
        children: list[BaseWidget] = []
        for index, shortcut in enumerate(hyprland_settings.get_custom_shortcuts()):
            if index:
                children.append(
                    Widget.Separator(css_classes=["settings-row-separator"])
                )
            children.append(
                CustomShortcutRow(
                    shortcut.id,
                    on_remove=lambda value=shortcut.id: self._remove(value),
                )
            )
        if not children:
            children.append(
                Widget.Label(
                    label="No custom shortcuts",
                    halign="start",
                    css_classes=["settings-custom-shortcuts-empty"],
                )
            )
        util.replace_box_children(self._rows, children)


class SettingsWindow(Widget.RegularWindow):
    def __init__(self):
        self.color_chooser: Gtk.ColorChooserDialog | None = None
        self.suggested_accent_colours = Widget.Box(
            css_classes=["settings-suggested-accent-colours"],
            spacing=10,
            halign="start",
            valign="center",
            vexpand=False,
            margin_top=10,
            margin_bottom=14,
        )
        self.suggested_accent_colours_content = Widget.Box(
            vertical=True,
            child=[self.suggested_accent_colours],
            height_request=52,
            hexpand=True,
        )
        self.suggested_accent_colours_scroll = Widget.Scroll(
            child=self.suggested_accent_colours_content,
            hexpand=True,
            halign="fill",
            hscrollbar_policy="automatic",
            vscrollbar_policy="never",
        )
        accent_adjustment = self.suggested_accent_colours_scroll.get_hadjustment()
        accent_adjustment.connect("changed", self._sync_accent_colours_alignment)
        GLib.idle_add(
            lambda: (
                self._sync_accent_colours_alignment(accent_adjustment),
                False,
            )[1]
        )
        self.custom_accent_colours = Widget.Box(
            css_classes=["settings-custom-accent-colours"],
            spacing=10,
            halign="start",
            valign="center",
            vexpand=False,
            margin_top=10,
            margin_bottom=14,
        )
        self.custom_accent_colours_content = Widget.Box(
            vertical=True,
            child=[self.custom_accent_colours],
            height_request=52,
            hexpand=True,
        )
        self.custom_accent_colours_scroll = Widget.Scroll(
            child=self.custom_accent_colours_content,
            hexpand=True,
            halign="fill",
            hscrollbar_policy="automatic",
            vscrollbar_policy="never",
        )
        custom_accent_adjustment = self.custom_accent_colours_scroll.get_hadjustment()
        custom_accent_adjustment.connect(
            "changed",
            lambda adjustment, *_: self._sync_colour_row_alignment(
                adjustment, self.custom_accent_colours
            ),
        )
        GLib.idle_add(
            lambda: (
                self._sync_colour_row_alignment(
                    custom_accent_adjustment, self.custom_accent_colours
                ),
                False,
            )[1]
        )
        self._render_custom_accent_colours()
        self.wallpapers_box = Widget.Box(
            vexpand=True,
            css_classes=["settings-wallpapers-box"],
        )
        style_settings.connect("notify::wallpaper", self._render_wallpapers)
        style_settings.connect("notify::addedwallpapers", self._render_wallpapers)
        self._render_wallpapers()
        self.wallpapers_scroll = Widget.Scroll(
            child=self.wallpapers_box,
            hexpand=True,
            hscrollbar_policy="automatic",
            vscrollbar_policy="never",
            css_classes=["settings-wallpapers-scroll"],
        )

        util.create_task(
            self.update_suggested_accent_colours(style_settings.wallpaper)
        )

        add_wallpaper_dialog = Widget.FileDialog(
            on_file_set=lambda _, file: style_settings.add_wallpaper(file),
            select_folder=False,
            filters=[
                Widget.FileFilter(
                    mime_types=["image/jpeg", "image/png", "image/webp"],
                    default=True,
                    name="Image",
                )
            ],
        )

        self.post_accent_change_entry = Widget.Entry(
            on_change=lambda _: style_settings.set_post_accent_change_cmd(
                self.post_accent_change_entry.get_text()
            )
        )
        self.post_accent_change_entry.set_text(style_settings.post_accent_change_cmd)

        appearance = SettingsPage(
            title="Appearance",
            description="Personalise the shell while keeping a calm, consistent desktop.",
            child=[
                SettingsGroup(
                    title="Wallpaper",
                    description="Choose a background from your library.",
                    child=[
                        Widget.Box(
                            vertical=True,
                            spacing=12,
                            child=[
                                self.wallpapers_scroll,
                                Widget.Box(
                                    halign="start",
                                    child=[
                                        Widget.Button(
                                            child=Widget.Box(
                                                spacing=7,
                                                child=[
                                                    Widget.Icon(
                                                        image="list-add-symbolic",
                                                        pixel_size=16,
                                                    ),
                                                    Widget.Label(label="Add wallpaper"),
                                                ],
                                            ),
                                            on_click=lambda _: util.create_task(
                                                add_wallpaper_dialog.open_dialog()
                                            ),
                                            css_classes=[
                                                "settings-secondary-button",
                                                "settings-wallpaper-button",
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                            css_classes=["settings-feature-content"],
                        ),
                    ],
                ),
                SettingsGroup(
                    title="Accent colour",
                    description="Suggested colours are extracted from your current wallpaper.",
                    child=[
                        Setting(
                            widget=self.suggested_accent_colours_scroll,
                            label="Suggested colours",
                            subtitle="Pick a colour that complements your background.",
                            icon="applications-graphics-symbolic",
                            label_hexpand=False,
                        ),
                        Setting(
                            widget=self.custom_accent_colours_scroll,
                            label="Custom colours",
                            subtitle="Use + to add a colour. Right-click one to remove it.",
                            icon="color-select-symbolic",
                            label_hexpand=False,
                        ),
                        Setting(
                            widget=Widget.Button(
                                label="Reset",
                                on_click=lambda _: self._reset_accent_colour(),
                                css_classes=["settings-secondary-button"],
                            ),
                            label="Reset accent colour",
                            subtitle="Return to the shell default.",
                            icon="edit-undo-symbolic",
                        ),
                        Setting(
                            widget=self.post_accent_change_entry,
                            label="After changing accent",
                            subtitle="Optional command to run after the theme is updated.",
                            icon="utilities-terminal-symbolic",
                        ),
                    ],
                ),
            ],
        )

        shell = SettingsPage(
            title="Shell",
            description="Control the bar, clock, workspaces and launcher.",
            child=[
                SettingsGroup(
                    title="Top bar",
                    description="Choose what appears in the shell’s persistent status area.",
                    child=[
                        SwitchWithLabel(
                            label="24-hour clock",
                            subtitle="Use regional 24-hour time formatting.",
                            icon="preferences-system-time-symbolic",
                            active=clock_settings.use_24h,
                            on_change=lambda _, active: clock_settings.set_use_24h(active),
                        ),
                        SwitchWithLabel(
                            label="Day of the week",
                            subtitle="Show the abbreviated weekday beside the date.",
                            icon="x-office-calendar-symbolic",
                            active=clock_settings.show_dow,
                            on_change=lambda _, active: clock_settings.set_show_dow(active),
                        ),
                        SwitchWithLabel(
                            label="Seconds",
                            subtitle="Include seconds in the top-bar clock.",
                            icon="preferences-system-time-symbolic",
                            active=clock_settings.show_seconds,
                            on_change=lambda _, active: clock_settings.set_show_seconds(active),
                        ),
                        SwitchWithLabel(
                            label="Battery percentage",
                            subtitle="Place the remaining percentage beside the battery icon.",
                            icon="battery-symbolic",
                            active=tray_settings.show_batt_percent,
                            on_change=lambda _, active: tray_settings.set_show_batt_percent(active),
                        ),
                    ],
                ),
                SettingsGroup(
                    title="Launcher components",
                    description="Choose which features are available in the launcher.",
                    child=[
                        SwitchWithLabel(
                            label="Applications",
                            subtitle="Search for installed applications.",
                            icon="system-search-symbolic",
                            active=True,
                            sensitive=False,
                        ),
                        SwitchWithLabel(
                            label="Calculator",
                            subtitle="Evaluate mathematical expressions.",
                            icon="accessories-calculator-symbolic",
                            active=launcher_settings.calculator_enabled,
                            on_change=lambda _, active: launcher_settings.set_calculator_enabled(active),
                        ),
                        SwitchWithLabel(
                            label="Currency conversion",
                            subtitle="Convert amounts between currencies.",
                            icon="accessories-calculator-symbolic",
                            active=launcher_settings.currency_enabled,
                            on_change=lambda _, active: launcher_settings.set_currency_enabled(active),
                        ),
                        SwitchWithLabel(
                            label="Power actions",
                            subtitle="Show shutdown, restart, logout and suspend actions.",
                            icon="system-shutdown-symbolic",
                            active=launcher_settings.power_actions_enabled,
                            on_change=lambda _, active: launcher_settings.set_power_actions_enabled(active),
                        ),
                    ],
                ),
                SettingsGroup(
                    title="Launcher component settings",
                    description="Configure the enabled launcher components.",
                    child=[
                        Setting(
                            widget=StringDropdown(
                                labels=CURRENCY_CODES,
                                enable_search=True,
                                on_change=launcher_settings.set_preferred_currency,
                                get_current=lambda: launcher_settings.preferred_currency,
                                settings_obj=launcher_settings,
                                notify_props=["preferred-currency"],
                            ),
                            label="Preferred currency",
                            subtitle="Target currency used when a conversion omits one.",
                            icon="accessories-calculator-symbolic",
                            sensitive=launcher_settings.bind("currency_enabled"),
                        ),
                    ],
                ),
            ],
        )

        keyboard_layouts = KeyboardLayoutsEditor()
        add_keyboard_layout = Widget.Button(
            label="Add layout",
            css_classes=["settings-secondary-button"],
            on_click=lambda *_: keyboard_layouts.add(),
        )
        from widgets.Settings.displays import build_displays_page

        displays = build_displays_page(SettingsPage, hyprland_settings)

        audio = SettingsPage(
            title="Audio",
            description="Choose audio devices and control system and application volume.",
            child=[
                SettingsGroup(
                    title="Output",
                    description="Select speakers or headphones and adjust playback.",
                    child=[
                        AudioDeviceList("speaker", self._open_connection_editor),
                    ],
                ),
                SettingsGroup(
                    title="Input",
                    description="Select a microphone and adjust recording volume.",
                    child=[
                        AudioDeviceList("microphone", self._open_connection_editor),
                    ],
                ),
                SettingsGroup(
                    title="Applications",
                    description="Control applications that currently have an audio stream.",
                    child=[ApplicationVolumeList()],
                ),
            ],
        )

        system_information = SettingsPage(
            title="System Information",
            description="Hardware, operating system, and shell information.",
            child=[
                SettingsGroup(
                    title="About this system",
                    description="",
                    child=[
                        Setting(
                            label=label,
                            icon=icon,
                            widget=Widget.Label(
                                label=value,
                                selectable=True,
                                wrap=False,
                                ellipsize="end",
                                hexpand=True,
                                halign="end",
                                xalign=1,
                                css_classes=["settings-system-info-value"],
                            ),
                        )
                        for label, value, icon in _system_information()
                    ],
                )
            ],
        )

        self._connection_editor: ConnectionEditorWindow | None = None
        self._new_wifi_connections = NewWifiConnections()
        self._new_bluetooth_connections = NewBluetoothConnections()
        self._saved_wifi_connections = SavedWifiConnections(
            self._open_connection_editor
        )
        self._saved_bluetooth_connections = SavedBluetoothConnections(
            self._open_connection_editor
        )
        self._saved_wifi_connections_scroll = CompactConnectionScroll(
            self._saved_wifi_connections,
            visible=network_service.wifi.bind("enabled"),
        )
        self._saved_bluetooth_connections_scroll = CompactConnectionScroll(
            self._saved_bluetooth_connections,
            visible=bluetooth_service.bind("powered"),
        )
        self._new_wifi_connections_scroll = CompactConnectionScroll(
            self._new_wifi_connections,
            visible=network_service.wifi.bind("enabled"),
        )
        self._new_bluetooth_connections_scroll = CompactConnectionScroll(
            self._new_bluetooth_connections,
            visible=bluetooth_service.bind("setup_mode"),
        )
        wireless = SettingsPage(
            title="Wi-Fi and Bluetooth",
            description="Manage saved connections and paired devices, or discover new ones.",
            child=[
                SettingsGroup(
                    title="Airplane mode",
                    description="",
                    child=[AirplaneModeSetting()],
                ),
                SettingsGroup(
                    title="Wi-Fi",
                    description="",
                    child=[
                        SwitchWithLabel(
                            label="Wi-Fi",
                            subtitle="Enable wireless networking.",
                            icon="network-wireless-symbolic",
                            active=network_service.wifi.bind("enabled"),
                            on_change=lambda _, active: network_service.wifi.set_enabled(active),
                        ),
                        Widget.Label(
                            label="Saved networks",
                            halign="start",
                            visible=network_service.wifi.bind("enabled"),
                            css_classes=["settings-connection-section-title"],
                        ),
                        self._saved_wifi_connections_scroll,
                        Setting(
                            widget=Widget.Button(
                                label="Scan",
                                on_click=lambda _: self._new_wifi_connections.scan(),
                                sensitive=network_service.wifi.bind("enabled"),
                                css_classes=["settings-secondary-button"],
                            ),
                            label="Find networks",
                            subtitle="Refresh the list of nearby Wi-Fi networks.",
                            icon="view-refresh-symbolic",
                            sensitive=network_service.wifi.bind("enabled"),
                        ),
                        Widget.Label(
                            label="Available networks",
                            halign="start",
                            visible=network_service.wifi.bind("enabled"),
                            css_classes=["settings-connection-section-title"],
                        ),
                        self._new_wifi_connections_scroll,
                    ],
                ),
                SettingsGroup(
                    title="Bluetooth",
                    description="",
                    child=[
                        SwitchWithLabel(
                            label="Bluetooth",
                            subtitle="Enable the Bluetooth adapter.",
                            icon="bluetooth-symbolic",
                            active=bluetooth_service.bind("powered"),
                            on_change=lambda _, active: bluetooth_service.set_powered(active),
                        ),
                        Widget.Label(
                            label="Paired devices",
                            halign="start",
                            visible=bluetooth_service.bind("powered"),
                            css_classes=["settings-connection-section-title"],
                        ),
                        self._saved_bluetooth_connections_scroll,
                        SwitchWithLabel(
                            label="Pair new devices",
                            subtitle="Make this computer discoverable and scan nearby devices.",
                            icon="list-add-symbolic",
                            active=bluetooth_service.bind("setup_mode"),
                            sensitive=bluetooth_service.bind("powered"),
                            on_change=lambda _, active: bluetooth_service.set_setup_mode(active),
                        ),
                        Widget.Label(
                            label="Available devices",
                            halign="start",
                            visible=bluetooth_service.bind("setup_mode"),
                            css_classes=["settings-connection-section-title"],
                        ),
                        self._new_bluetooth_connections_scroll,
                    ],
                ),
            ],
        )

        devices = SettingsPage(
            title="Devices",
            description="Configure keyboard and pointer input used by Hyprland.",
            child=[
                SettingsGroup(
                    title="Keyboard",
                    description="Add layouts and choose an optional variant for each one.",
                    child=[
                        Setting(
                            widget=add_keyboard_layout,
                            label="Add keyboard layout",
                            subtitle="The first configured layout is used by default.",
                            icon="input-keyboard-symbolic",
                        ),
                    ],
                ),
                SettingsGroup(
                    title="Configured layouts",
                    description="Choose the layout and variant used for each entry.",
                    child=[keyboard_layouts],
                ),
                SettingsGroup(
                    title="Pointer",
                    description="Tune pointer movement without leaving the shell.",
                    child=[
                        Setting(
                            widget=Widget.Scale(
                                min=-1.0,
                                max=1.0,
                                step=0.1,
                                value=hyprland_settings.bind("pointer_sensitivity"),
                                on_change=lambda scale: hyprland_settings.set_pointer_sensitivity(
                                    scale.get_value()
                                ),
                                css_classes=["settings-pointer-speed-scale"],
                            ),
                            label="Pointer speed",
                            subtitle="Slower to the left, faster to the right.",
                            icon="input-mouse-symbolic",
                        ),
                        SwitchWithLabel(
                            label="Pointer acceleration",
                            subtitle="Adapt movement speed to how quickly the pointer moves.",
                            icon="input-mouse-symbolic",
                            active=hyprland_settings.bind("acceleration_enabled"),  # type: ignore
                            on_change=lambda _, active: hyprland_settings.set_acceleration_enabled(active),
                        ),
                    ],  # type: ignore
                ),
            ],
        )

        program_rows = []
        for name, label, subtitle, icon in (
            ("terminal", "Terminal", "Command launched by the terminal shortcut.", "utilities-terminal-symbolic"),
            ("file_manager", "File manager", "Command launched by the file manager shortcut.", "system-file-manager-symbolic"),
            ("browser", "Web browser", "Command launched by the browser shortcut.", "web-browser-symbolic"),
            ("editor", "Text editor", "Value exported as the EDITOR environment variable.", "accessories-text-editor-symbolic"),
        ):
            program_rows.append(
                Setting(
                    widget=Widget.Entry(
                        text=getattr(hyprland_settings, f"program_{name}"),
                        hexpand=False,
                        width_chars=42,
                        max_width_chars=42,
                        on_change=lambda entry, setting=name: hyprland_settings.set_program(
                            setting, entry.text
                        ),
                        css_classes=["settings-command-entry"],
                    ),
                    label=label,
                    subtitle=subtitle,
                    icon=icon,
                )
            )

        default_applications = SettingsPage(
            title="Default Applications",
            description="Choose the programs used by the desktop.",
            child=[
                SettingsGroup(
                    title="Applications",
                    description="Commands are applied automatically.",
                    child=program_rows,
                ),
            ],
        )

        shortcut_groups: list[BaseWidget] = [
            SettingsGroup(
                title="Shortcut modifiers",
                description="Each shortcut uses its own combination of Shift, Ctrl, Alt and Super.",
                child=[
                    Setting(
                        widget=Widget.Button(
                            label="Swap Alt and Super",
                            on_click=lambda _: (
                                hyprland_settings.swap_alt_super(),
                                KeybindingEditor.sync_all_modifiers(),
                            ),
                            css_classes=["settings-secondary-button"],
                        ),
                        label="Swap shortcut modifiers",
                        subtitle="Exchange Alt and Super across every shortcut.",
                        icon="input-keyboard-symbolic",
                    ),
                ],
            ),
        ]
        visible_keybindings = hyprland_settings.get_keybind_definitions()
        categories = list(dict.fromkeys(item.category for item in visible_keybindings))
        for category in categories:
            if category == "Workspaces":
                workspace_shortcuts = Widget.Box(vertical=True)

                def render_workspace_shortcuts(*_args) -> None:
                    definitions = [
                        definition
                        for definition in hyprland_settings.get_keybind_definitions()
                        if definition.category == "Workspaces"
                    ]
                    util.replace_box_children(
                        workspace_shortcuts,
                        [
                            SettingsGroup(
                                title="Workspaces",
                                description="",
                                child=[
                                    Setting(
                                        widget=KeybindingEditor(definition.action),
                                        label=definition.label,
                                    )
                                    for definition in definitions
                                ],
                            )
                        ],
                    )

                hyprland_settings.connect(
                    "notify::workspace-count", render_workspace_shortcuts
                )
                render_workspace_shortcuts()
                shortcut_groups.append(workspace_shortcuts)
            else:
                shortcut_groups.append(
                    SettingsGroup(
                        title=category,
                        description="",
                        child=[
                            Setting(
                                widget=KeybindingEditor(definition.action),
                                label=definition.label,
                            )
                            for definition in visible_keybindings
                            if definition.category == category
                        ],
                    )
                )

        shortcut_groups.append(
            SettingsGroup(
                title="Custom shortcuts",
                description="Run a shell command in the background with any key combination.",
                child=[CustomShortcutsEditor()],
            )
        )

        shortcuts = SettingsPage(
            title="Shortcuts",
            description="Customise desktop keyboard shortcuts.",
            child=shortcut_groups,
        )

        workspace_count = Gtk.SpinButton.new_with_range(1, 10, 1)
        workspace_count.set_value(hyprland_settings.workspace_count)
        workspace_count.set_width_chars(2)
        workspace_count.set_valign(Gtk.Align.CENTER)
        workspace_count.add_css_class("settings-workspace-count")
        workspace_count.connect(
            "value-changed",
            lambda spin: hyprland_settings.set_workspace_count(
                spin.get_value_as_int()
            ),
        )

        def sync_workspace_count(*_args) -> None:
            value = hyprland_settings.workspace_count
            if workspace_count.get_value_as_int() != value:
                workspace_count.set_value(value)

        hyprland_settings.connect(
            "notify::workspace-count", sync_workspace_count
        )

        workspace_scope = Widget.Switch(
            active=hyprland_settings.workspaces_span_displays,
            valign="center",
        )
        workspace_scope.connect(
            "state-set",
            lambda _, state: (
                hyprland_settings.set_workspaces_span_displays(bool(state)),
                False,
            )[1],
        )
        hide_empty_workspaces = Widget.Switch(
            active=hyprland_settings.hide_empty_workspaces,
            valign="center",
        )
        hide_empty_workspaces.connect(
            "state-set",
            lambda _, state: (
                hyprland_settings.set_hide_empty_workspaces(bool(state)),
                False,
            )[1],
        )

        windows = SettingsPage(
            title="Windows & Workspaces",
            description="Choose how windows are arranged and how workspaces behave across displays.",
            child=[
                SettingsGroup(
                    title="Workspaces",
                    description="Workspaces are presented as one fixed logical set, independent of Hyprland’s internal per-monitor workspaces.",
                    child=[
                        Setting(
                            widget=workspace_scope,
                            label="Workspaces span all displays",
                            subtitle="When off, only the primary display switches and secondary displays keep their content.",
                            icon="video-display-symbolic",
                        ),
                        Setting(
                            widget=cast(BaseWidget, workspace_count),
                            label="Number of workspaces",
                            subtitle="Sets the dots in the bar and the workspace shortcuts shown in Settings.",
                            icon="view-grid-symbolic",
                        ),
                        Setting(
                            widget=hide_empty_workspaces,
                            label="Hide empty workspaces in the bar",
                            subtitle="The active workspace remains visible even when it has no windows.",
                            icon="view-conceal-symbolic",
                        ),
                    ],
                ),
                SettingsGroup(
                    title="Tiling",
                    description="Hyprland provides two distinct automatic tiling strategies.",
                    child=[
                        Setting(
                            widget=StringDropdown(
                                labels=[layout.capitalize() for layout in hyprland_layouts],
                                on_change=lambda value: hyprland_settings.set_layout_type(
                                    value.lower()
                                ),
                                get_current=lambda: hyprland_settings.layout_type.capitalize(),
                                settings_obj=hyprland_settings,
                                notify_props=["layout-type"],
                            ),
                            label="Layout algorithm",
                            subtitle="Dwindle recursively splits space; Master reserves a primary area.",
                            icon="view-grid-symbolic",
                        ),
                        Setting(
                            widget=Widget.Button(
                                label="Open documentation",
                                on_click=lambda _: util.shell(
                                    "xdg-open https://wiki.hypr.land/Configuring/Layouts/"
                                ),
                                css_classes=["settings-secondary-button"],
                            ),
                            label="Learn about layouts",
                            subtitle="Read Hyprland’s layout configuration guide.",
                            icon="help-browser-symbolic",
                        ),
                    ],
                ),
            ],
        )

        def timeout_control(
            attribute: str,
            setter: Callable[[int], None],
            enabled_attribute: str,
            enabled_setter: Callable[[bool], None],
        ):
            spin = Gtk.SpinButton.new_with_range(1, 240, 1)
            spin.set_value(getattr(power_settings, attribute))
            spin.set_width_chars(4)
            spin.set_valign(Gtk.Align.CENTER)
            spin.connect(
                "value-changed", lambda value: setter(value.get_value_as_int())
            )

            time_control = Widget.Box(
                spacing=8,
                valign="center",
                sensitive=getattr(power_settings, enabled_attribute),
                child=[
                    cast(BaseWidget, spin),
                    Widget.Label(label="minutes"),
                ],
            )
            enabled = Widget.Switch(
                active=getattr(power_settings, enabled_attribute),
                valign="center",
            )

            def sync_value(*_args) -> None:
                current = getattr(power_settings, attribute)
                if spin.get_value_as_int() != current:
                    spin.set_value(current)

            def sync_enabled(*_args) -> None:
                current = getattr(power_settings, enabled_attribute)
                if enabled.active != current:
                    enabled.active = current
                time_control.sensitive = current

            def set_enabled(_switch, state: bool) -> bool:
                time_control.sensitive = bool(state)
                enabled_setter(bool(state))
                return False

            power_settings.connect(
                f"notify::{attribute.replace('_', '-')}", sync_value
            )
            power_settings.connect(
                f"notify::{enabled_attribute.replace('_', '-')}", sync_enabled
            )
            enabled.connect("state-set", set_enabled)
            return Widget.Box(
                spacing=14,
                valign="center",
                child=[
                    enabled,
                    time_control,
                ],
            )

        power = SettingsPage(
            title="Power Management",
            description="Choose when an idle session blanks, locks and suspends.",
            child=[
                SettingsGroup(
                    title="Power mode",
                    description="Balance performance and energy use.",
                    child=[
                        Setting(
                            widget=(
                                StringDropdown(
                                    labels=[],
                                    choices=[
                                        KeyboardChoice(
                                            value=profile,
                                            label=transform_power_profile_name(profile),
                                        )
                                        for profile in power_profiles.profiles
                                    ],
                                    on_change=set_power_profile,
                                    get_current=lambda: power_profiles.active_profile,
                                )
                                if power_profiles.is_available
                                else Widget.Label(label="Unavailable")
                            ),
                            label="Power mode",
                            subtitle="Select the system power profile.",
                            icon="power-profile-balanced-symbolic",
                        ),
                    ],
                ),
                SettingsGroup(
                    title="Idle timeouts",
                    description="Times are in minutes and changes apply automatically.",
                    child=[
                        Setting(
                            widget=timeout_control(
                                "display_timeout_minutes",
                                power_settings.set_display_timeout_minutes,
                                "display_timeout_enabled",
                                power_settings.set_display_timeout_enabled,
                            ),
                            label="Turn screen off",
                            subtitle="Blank inactive displays after this many minutes.",
                            icon="video-display-symbolic",
                        ),
                        Setting(
                            widget=timeout_control(
                                "lock_timeout_minutes",
                                power_settings.set_lock_timeout_minutes,
                                "lock_timeout_enabled",
                                power_settings.set_lock_timeout_enabled,
                            ),
                            label="Lock session",
                            subtitle="Show the lock screen after this many minutes.",
                            icon="system-lock-screen-symbolic",
                        ),
                        Setting(
                            widget=timeout_control(
                                "suspend_timeout_minutes",
                                power_settings.set_suspend_timeout_minutes,
                                "suspend_timeout_enabled",
                                power_settings.set_suspend_timeout_enabled,
                            ),
                            label="Suspend system",
                            subtitle="Suspend the computer after this many minutes.",
                            icon="media-playback-pause-symbolic",
                        ),
                    ],
                ),
            ],
        )

        backup = SettingsPage(
            title="Backup & Restore",
            description="Move your desktop preferences between installations.",
            child=[
                SettingsGroup(
                    title="Settings profile",
                    description="The JSON profile contains shell, appearance, shortcut, workspace, application and power preferences. Wallpaper image files and display hardware configuration stay local.",
                    child=[
                        Setting(
                            widget=Widget.Button(
                                label="Export…",
                                on_click=lambda *_: util.create_task(
                                    self._export_settings()
                                ),
                                css_classes=["settings-secondary-button"],
                            ),
                            label="Export settings",
                            subtitle="Save a readable JSON profile.",
                            icon="document-save-symbolic",
                        ),
                        Setting(
                            widget=Widget.Button(
                                label="Import…",
                                on_click=lambda *_: util.create_task(
                                    self._import_settings()
                                ),
                                css_classes=["settings-secondary-button"],
                            ),
                            label="Import settings",
                            subtitle="Restore a profile exported by this desktop.",
                            icon="document-open-symbolic",
                        ),
                    ],
                ),
            ],
        )

        page_specs = [
            ("Appearance", "preferences-desktop-wallpaper-symbolic", appearance),
            ("Shell", "preferences-system-symbolic", shell),
            ("Displays", "preferences-desktop-display-symbolic", displays),
            ("Audio", "audio-speakers-symbolic", audio),
            ("Wi-Fi and Bluetooth", "network-wireless-symbolic", wireless),
            ("Devices", "input-keyboard-symbolic", devices),
            (
                "Default Applications",
                "application-x-executable-symbolic",
                default_applications,
            ),
            ("Shortcuts", "preferences-desktop-keyboard-shortcuts-symbolic", shortcuts),
            ("Windows & Workspaces", "focus-windows-symbolic", windows),
            ("Power Management", "battery-symbolic", power),
            ("System Information", "computer-symbolic", system_information),
            ("Backup & Restore", "document-save-symbolic", backup),
        ]
        self._page_titles = [title for title, _, _ in page_specs]
        self._page_widgets = [
            Widget.Scroll(
                child=page,
                hexpand=True,
                vexpand=True,
                hscrollbar_policy="never",
                vscrollbar_policy="automatic",
                css_classes=["settings-page-scroll"],
            )
            for _, _, page in page_specs
        ]
        self._settings_stack = Widget.Stack(
            child=[
                Widget.StackPage(title=title, child=page)
                for (title, _, _), page in zip(page_specs, self._page_widgets)
            ],
            transition_type="crossfade",
            transition_duration=180,
            hexpand=True,
            vexpand=True,
            css_classes=["settings-stack"],
        )
        self._page_buttons: list[Widget.Button] = []
        navigation: list[BaseWidget] = []
        for index, (title, icon, _) in enumerate(page_specs):
            button = Widget.Button(
                child=Widget.Box(
                    spacing=12,
                    child=[
                        Widget.Icon(image=icon, pixel_size=18),
                        Widget.Label(label=title, halign="start", hexpand=True),
                    ],
                ),
                on_click=lambda _, selected=index: self._select_page(selected),
                css_classes=["settings-sidebar-button"],
            )
            self._page_buttons.append(button)
            navigation.append(button)

        sidebar_content = Widget.Box(
            vertical=True,
            spacing=4,
            child=[
                *navigation[:-1],
                Widget.Box(vexpand=True),
                Widget.Separator(css_classes=["settings-sidebar-separator"]),
                navigation[-1],
                Widget.Button(
                    child=Widget.Box(
                        spacing=10,
                        child=[
                            Widget.Icon(image="view-refresh-symbolic", pixel_size=17),
                            Widget.Label(label="Reload shell"),
                        ],
                    ),
                    on_click=lambda _: util.shell("goignis reload"),
                    css_classes=["settings-reload-button"],
                ),
            ],
        )
        sidebar = Widget.Box(
            vertical=True,
            spacing=4,
            child=[
                Widget.Scroll(
                    child=sidebar_content,
                    hexpand=True,
                    vexpand=True,
                    min_content_height=1,
                    hscrollbar_policy="never",
                    vscrollbar_policy="automatic",
                    css_classes=["settings-sidebar-scroll"],
                ),
            ],
            css_classes=["settings-sidebar"],
        )

        self._select_page(0)
        super().__init__(
            child=Widget.Box(
                child=[sidebar, self._settings_stack],
                css_classes=["settings"],
            ),
            titlebar=Widget.HeaderBar(
                title_widget=Widget.Label(
                    label="Settings",
                    css_classes=["settings-header-title"],
                ),
                show_title_buttons=True,
                css_classes=["settings-headerbar"],
            ),
            title="Ignis Settings",
            default_width=980,
            default_height=720,
            namespace="ignis_settings",
            css_classes=["window", "settings-window"],
            visible=False,
            hide_on_close=True,
        )

    def _settings_profile(self) -> dict[str, Any]:
        hyprland = hyprland_settings.export_data()
        hyprland["keybindings"] = json.loads(
            hyprland.pop("keybindings_json")
        )
        hyprland["custom_shortcuts"] = json.loads(
            hyprland.pop("custom_shortcuts_json")
        )

        style = style_settings.export_data()
        style["added_wallpapers"] = style_settings._added_wallpapers_str_to_list(
            style.pop("addedwallpapers")
        )
        raw_custom_colours = style.pop("custom_accent_colours")
        style["custom_accent_colours"] = (
            json.loads(raw_custom_colours) if raw_custom_colours else {}
        )
        try:
            style["accent_colour"] = style_settings.get_accent_colour(
                style_settings.wallpaper
            )
        except OSError:
            style["accent_colour"] = None

        apps = app_settings.export_data()
        raw_hidden_apps = apps.pop("hidden_apps")
        apps["hidden_apps"] = (
            json.loads(raw_hidden_apps) if raw_hidden_apps else []
        )

        return {
            "format": "marzeq-desktop-settings",
            "version": 1,
            "settings": {
                "hyprland": hyprland,
                "style": style,
                "clock": clock_settings.export_data(),
                "launcher": launcher_settings.export_data(),
                "tray": tray_settings.export_data(),
                "applications": apps,
                "power": power_settings.export_data(),
            },
        }

    def _show_transfer_error(self, detail: str) -> None:
        dialog = Gtk.AlertDialog()
        dialog.set_message("Settings transfer failed")
        dialog.set_detail(detail)
        dialog.show(self)

    async def _export_settings(self) -> None:
        dialog = Gtk.FileDialog()
        dialog.set_title("Export desktop settings")
        dialog.set_initial_name("marzeq-desktop-settings.json")
        try:
            selected = await dialog.save(self)  # type: ignore
        except GLib.Error:
            return
        if selected is None or selected.get_path() is None:
            return
        try:
            path = Path(selected.get_path())
            write_atomic(path, json.dumps(self._settings_profile(), indent=2) + "\n")
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._show_transfer_error(f"Could not export settings: {exc}")
            return

    @staticmethod
    def _profile_sections(profile: Any) -> dict[str, dict[str, Any]]:
        if not isinstance(profile, dict):
            raise ValueError("The profile root must be a JSON object")
        if profile.get("format") != "marzeq-desktop-settings":
            raise ValueError("This is not a marzeq desktop settings profile")
        if profile.get("version") != 1:
            raise ValueError("This settings profile version is not supported")
        sections = profile.get("settings")
        if not isinstance(sections, dict):
            raise ValueError("The profile has no settings object")
        required = {
            "hyprland",
            "style",
            "clock",
            "launcher",
            "tray",
            "applications",
            "power",
        }
        if set(sections) != required:
            raise ValueError("The profile has missing or unknown settings sections")
        if not all(isinstance(section, dict) for section in sections.values()):
            raise ValueError("Every settings section must be a JSON object")
        return cast(dict[str, dict[str, Any]], sections)

    async def _import_settings(self) -> None:
        dialog = Gtk.FileDialog()
        dialog.set_title("Import desktop settings")
        try:
            selected = await dialog.open(self)  # type: ignore
        except GLib.Error:
            return
        if selected is None or selected.get_path() is None:
            return

        settings_objects: dict[str, BindableSettings] = {
            "hyprland": hyprland_settings,
            "style": style_settings,
            "clock": clock_settings,
            "launcher": launcher_settings,
            "tray": tray_settings,
            "applications": app_settings,
            "power": power_settings,
        }
        snapshots = {
            name: settings.export_data()
            for name, settings in settings_objects.items()
        }
        imported_wallpaper_exists = False
        accent_colour: str | None = None
        try:
            path = Path(selected.get_path())
            profile = json.loads(path.read_text(encoding="utf-8"))
            sections = self._profile_sections(profile)

            hyprland = dict(sections["hyprland"])
            hyprland["keybindings_json"] = json.dumps(
                hyprland.pop("keybindings"), separators=(",", ":")
            )
            hyprland["custom_shortcuts_json"] = json.dumps(
                hyprland.pop("custom_shortcuts"), separators=(",", ":")
            )
            monitor_names = {monitor.name for monitor in util.hyprland.monitors}
            if hyprland.get("primary_monitor") not in monitor_names:
                hyprland["primary_monitor"] = hyprland_settings.primary_monitor

            style = dict(sections["style"])
            accent_value = style.pop("accent_colour", None)
            if accent_value is not None and not isinstance(accent_value, str):
                raise TypeError("Accent colour must be a string or null")
            accent_colour = accent_value
            wallpapers = style.pop("added_wallpapers")
            if not isinstance(wallpapers, list) or not all(
                isinstance(item, str) for item in wallpapers
            ):
                raise TypeError("Added wallpapers must be a list of paths")
            style["addedwallpapers"] = style_settings._added_wallpapers_list_to_str(
                wallpapers
            )
            style["custom_accent_colours"] = json.dumps(
                style["custom_accent_colours"],
                separators=(",", ":"),
                sort_keys=True,
            )
            imported_wallpaper = style.get("wallpaper")
            imported_wallpaper_exists = (
                isinstance(imported_wallpaper, str)
                and Path(imported_wallpaper).is_file()
            )
            if not imported_wallpaper_exists:
                style["wallpaper"] = style_settings.wallpaper

            apps = dict(sections["applications"])
            hidden_apps = apps["hidden_apps"]
            if not isinstance(hidden_apps, list) or not all(
                isinstance(item, str) for item in hidden_apps
            ):
                raise TypeError("Hidden applications must be a list of names")
            apps["hidden_apps"] = json.dumps(hidden_apps, separators=(",", ":"))

            prepared = {
                **sections,
                "hyprland": hyprland,
                "style": style,
                "applications": apps,
            }
            for name, settings in settings_objects.items():
                settings.import_data(prepared[name])
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            for name, settings in settings_objects.items():
                try:
                    settings.import_data(snapshots[name])
                except (OSError, TypeError, ValueError):
                    pass
            self._show_transfer_error(f"Could not import settings: {exc}")
            return

        if imported_wallpaper_exists:
            util.shell("~/.config/hypr/scripts/set_curr_wallpaper.sh")
            if accent_colour:
                style_settings.set_accent_colour(
                    accent_colour, style_settings.wallpaper
                )
            else:
                style_settings.restore_accent_colour(style_settings.wallpaper)
        hyprland_settings.schedule_hyprland_reload()
        power_settings.restart()

    def _open_connection_editor(
        self, title: str, content: BaseWidget, actions: list[BaseWidget]
    ) -> None:
        if self._connection_editor is None:
            self._connection_editor = ConnectionEditorWindow(self)
        self._connection_editor.edit(title, content, actions)

    def _select_page(self, index: int) -> None:
        if not 0 <= index < len(self._page_widgets):
            return
        self._settings_stack.set_visible_child(self._page_widgets[index])
        for button_index, button in enumerate(self._page_buttons):
            classes = ["settings-sidebar-button"]
            if button_index == index:
                classes.append("active")
            button.css_classes = classes

    def select_page(self, title: str) -> None:
        try:
            index = self._page_titles.index(title)
        except ValueError:
            return
        self._select_page(index)

    def _sync_colour_row_alignment(self, adjustment, row) -> None:
        has_overflow = adjustment.get_upper() > adjustment.get_page_size() + 0.5
        Gtk.Widget.set_halign(row, Gtk.Align.START if has_overflow else Gtk.Align.END)

    def _sync_accent_colours_alignment(self, adjustment, *_args) -> None:
        self._sync_colour_row_alignment(adjustment, self.suggested_accent_colours)

    def _open_color_chooser(self, *_args) -> None:
        if self.color_chooser is not None:
            self.color_chooser.present()
            return

        self.color_chooser = Gtk.ColorChooserDialog(
            title="Pick a Colour",
            transient_for=self,
            modal=True,
            resizable=False,
        )
        self.color_chooser.set_use_alpha(False)
        self.color_chooser.connect("response", self._on_color_chooser_response)
        self.color_chooser.present()

    def _on_color_chooser_response(self, dialog, response, *_args) -> None:
        try:
            if response == Gtk.ResponseType.OK:
                style_settings.add_custom_accent_colour_from_rgba(
                    dialog.get_rgba(), style_settings.wallpaper
                )
                self._render_custom_accent_colours()
        except Exception:
            util.logger.exception("Failed to save custom accent colour")
        finally:
            dialog.destroy()
            if dialog is self.color_chooser:
                self.color_chooser = None

    def _render_wallpapers(self, *_args) -> None:
        util.replace_box_children(
            self.wallpapers_box,
            [
                WallpaperButton(
                    path,
                    self.on_wallpaper_picked,
                    self.on_wallpaper_removed,
                    path == style_settings.wallpaper,
                )
                for path in style_settings.get_wallpapers()
            ],
        )

    async def update_suggested_accent_colours(self, path: str):
        top_colours = await style_settings.get_cached_top_colours(path)
        selected_colour = style_settings.get_accent_colour(path)
        util.replace_box_children(
            self.suggested_accent_colours,
            [
                AccentColourButton(
                    colour=colour,
                    wallpaper=path,
                    selected=(
                        selected_colour is not None
                        and colour.lower() == selected_colour.lower()
                    ),
                    on_selected=self.on_suggested_accent_colour_selected,
                )
                for colour in top_colours
            ],
        )

    def on_suggested_accent_colour_selected(
        self, colour: str, wallpaper: str
    ) -> None:
        style_settings.set_accent_colour(colour, wallpaper)
        util.create_task(self.update_suggested_accent_colours(wallpaper))
        self._render_custom_accent_colours()

    def _render_custom_accent_colours(self, *_args) -> None:
        selected_colour = style_settings.get_accent_colour(style_settings.wallpaper)
        custom_buttons = [
            AccentColourButton(
                colour=colour,
                wallpaper=style_settings.wallpaper,
                selected=(
                    selected_colour is not None
                    and colour.lower() == selected_colour.lower()
                ),
                on_selected=self.on_suggested_accent_colour_selected,
                on_removed=self._remove_custom_accent_colour,
            )
            for colour in style_settings.list_custom_accent_colours(
                style_settings.wallpaper
            )
        ]
        custom_buttons.append(
            Widget.Button(
                child=Widget.Icon(image="list-add-symbolic", pixel_size=16),
                width_request=32,
                height_request=32,
                valign="center",
                vexpand=False,
                on_click=self._open_color_chooser,
                tooltip_text="Add custom colour",
                css_classes=[
                    "settings-suggested-accent-colour",
                    "settings-add-custom-accent-colour",
                ],
            )
        )
        util.replace_box_children(self.custom_accent_colours, custom_buttons)

    def _remove_custom_accent_colour(self, colour: str) -> None:
        wallpaper = style_settings.wallpaper
        selected_colour = style_settings.get_accent_colour(wallpaper)
        style_settings.remove_custom_accent_colour(colour, wallpaper)
        if (
            selected_colour is not None
            and selected_colour.lower() == colour.lower()
        ):
            style_settings.restore_accent_colour(wallpaper)
            util.create_task(self.update_suggested_accent_colours(wallpaper))
        self._render_custom_accent_colours()

    def _reset_accent_colour(self) -> None:
        wallpaper = style_settings.wallpaper
        style_settings.restore_accent_colour(wallpaper)
        util.create_task(self.update_suggested_accent_colours(wallpaper))
        self._render_custom_accent_colours()

    async def on_wallpaper_picked(self, file):
        await style_settings.pick_wallpaper(file)
        await self.update_suggested_accent_colours(file)
        self._render_custom_accent_colours()
        self.wallpapers_scroll.get_hadjustment().set_value(0)

    def on_wallpaper_removed(self, path):
        style_settings.remove_wallpaper(path)
