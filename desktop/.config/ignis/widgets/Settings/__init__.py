import asyncio
import os
from typing import Any, Callable, Literal, cast
from gi.repository import GLib, Gtk  # pyright: ignore[reportMissingModuleSource]
from ignis.base_widget import BaseWidget
from ignis.services.bluetooth import BluetoothDevice, BluetoothService
from ignis.services.network import NetworkService, WifiAccessPoint, WifiDevice
from ignis.widgets import Widget
from util import BindableSettings, JsonSettings
import util
from widgets.Settings.style_settings import style_settings
from widgets.Clock import clock_settings
from widgets.Workspaces import workspace_settings
from widgets.Launcher.currencies import CURRENCY_CODES
from widgets.Launcher.settings import launcher_settings
from widgets.Tray import tray_settings

network_service = NetworkService.get_default()
bluetooth_service = BluetoothService.get_default()

HyprlandLayout = Literal["master"] | Literal["dwindle"]
hyprland_layouts: list[HyprlandLayout] = ["master", "dwindle"]


@JsonSettings("hyprland")
class HyprlandSettings(BindableSettings):
    keyboard_layout: str = "us"
    keyboard_variant: str = ""

    def set_keyboard_layout(self, value: str) -> None:
        self.keyboard_layout = value

    def set_keyboard_variant(self, value: str) -> None:
        self.keyboard_variant = value

    layout_type: HyprlandLayout = "master"

    def set_layout_type(self, value: HyprlandLayout) -> None:
        self.layout_type = value

    pointer_sensitivity: float = 0.0
    acceleration_enabled: bool = False

    def set_pointer_sensitivity(self, value: float) -> None:
        self.pointer_sensitivity = value

    def set_acceleration_enabled(self, value: bool) -> None:
        self.acceleration_enabled = value

    def sync(self) -> None:
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

        sensitivity = {self.pointer_sensitivity},
        accel_profile = {
            '"flat"'
            if not self.acceleration_enabled
            else '"adaptive"'
        },
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

    primary_monitor: str = util.hyprland.monitors[0].name

    def set_primary_monitor(self, value: str) -> None:
        self.primary_monitor = value


hyprland_settings = HyprlandSettings()


@JsonSettings("bar")
class BarSettingsSettings(BindableSettings):
    show_only_on_primary_monitor: bool = False

    def set_show_only_on_primary_monitor(self, value: bool):
        self.show_only_on_primary_monitor = value


bar_settings = BarSettingsSettings()


def get_keyboard_layouts() -> list[str]:
    layouts = []
    with open("/usr/share/X11/xkb/rules/base.lst", "r") as f:
        lines = f.readlines()
        in_layouts_section = False
        for line in lines:
            line = line.strip()
            if line.startswith("! layout"):
                in_layouts_section = True
                continue
            if in_layouts_section:
                if line.startswith("!"):
                    break
                if line and not line.startswith("#"):
                    parts = line.split()
                    if parts and parts[0] not in layouts and parts[0] != "custom":
                        layouts.append(parts[0])
    return layouts


def get_keyboard_variants(layout: str) -> list[str]:
    variants: list[str] = [""]
    with open("/usr/share/X11/xkb/rules/base.lst", "r") as f:
        in_variants = False
        for raw in f:
            line = raw.rstrip()
            if line.startswith("! variant"):
                in_variants = True
                continue
            if in_variants:
                if line.startswith("!"):
                    break
                if not line or line.lstrip().startswith("#"):
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    variant = parts[0]
                    layout_part = parts[1]
                    if layout_part.endswith(":") and layout_part[:-1] == layout:
                        variants.append(variant)
    return variants


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


def _new_connection_row(
    *, icon: str, label: str, subtitle: str = "", on_click: Callable
) -> Widget.Button:
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


class NewWifiConnections(Widget.Box):
    def __init__(self) -> None:
        self._device: WifiDevice | None = None
        self._device_handler: int | None = None
        self._ap_handlers: list[tuple[WifiAccessPoint, int]] = []
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
            util.replace_box_children(
                self,
                [Widget.Label(label="Wi-Fi is turned off", css_classes=["settings-connection-empty"])],
            )
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
        rows: list[BaseWidget] = []
        for ap in access_points:
            for prop in ("strength", "icon-name", "ssid", "psk"):
                self._ap_handlers.append(
                    (ap, ap.connect(f"notify::{prop}", self._render))
                )
            security = ap.security or "Open network"
            rows.append(
                _new_connection_row(
                    icon=ap.icon_name,
                    label=ap.ssid or "Hidden network",
                    subtitle=security,
                    on_click=lambda _, access_point=ap: util.create_task(
                        access_point.connect_to_graphical()
                    ),
                )
            )
        util.replace_box_children(
            self,
            rows
            or [
                Widget.Label(
                    label="No new networks found",
                    css_classes=["settings-connection-empty"],
                )
            ],
        )


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

        devices = sorted(
            (device for device in bluetooth_service.devices if not device.paired),
            key=lambda device: (device.alias or device.name).casefold(),
        )
        rows: list[BaseWidget] = []
        for device in devices:
            for prop in ("paired", "connected", "alias", "name", "icon-name"):
                self._device_handlers.append(
                    (device, device.connect(f"notify::{prop}", self._render))
                )
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


def KeyboardLayoutDropdown() -> BaseWidget:
    layouts = get_keyboard_layouts()

    model = Gtk.StringList()
    for l in layouts:
        model.append(l)

    dropdown = Gtk.DropDown(
        model=model,
        expression=Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"),
    )
    dropdown.set_hexpand(False)
    dropdown.set_halign(Gtk.Align.START)
    dropdown.set_valign(Gtk.Align.CENTER)
    dropdown.add_css_class("settings-dropdown")
    dropdown.set_enable_search(True)

    def on_selected(dd, _):
        item = dd.get_selected_item()
        if item is not None:
            hyprland_settings.set_keyboard_layout(item.props.string)
            hyprland_settings.set_keyboard_variant("")

    dropdown.connect("notify::selected-item", on_selected)

    def sync_from_settings(*_):
        try:
            dropdown.set_selected(layouts.index(hyprland_settings.keyboard_layout))
        except ValueError:
            pass

    GLib.idle_add(lambda: (sync_from_settings(), False)[1])

    hyprland_settings.connect("notify::keyboard-layout", sync_from_settings)

    return dropdown  # type: ignore


def StringDropdown(
    *,
    labels: list[str],
    on_change: Callable,
    get_current: Callable | None = None,
    settings_obj=None,
    notify_props: list[str] | None = None,
    enable_search: bool = False,
    repopulate: Callable | None = None,
):
    model = Gtk.StringList()
    syncing = False

    def fill(items: list[str]):
        while model.get_n_items():
            model.remove(0)
        for i in items:
            model.append(i)

    fill(labels)

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
        item = dd.get_selected_item()
        if item:
            on_change(item.props.string)

    dropdown.connect("notify::selected-item", on_selected)

    def sync_from_settings(*_):
        nonlocal syncing
        if not get_current:
            return
        syncing = True

        current_labels = labels
        if repopulate:
            current_labels = repopulate()
            fill(current_labels)

        try:
            dropdown.set_selected(current_labels.index(get_current()))
        except ValueError:
            dropdown.set_selected(0)

        syncing = False

    GLib.idle_add(lambda: (sync_from_settings(), False)[1])

    if settings_obj and notify_props:
        for prop in notify_props:
            settings_obj.connect(f"notify::{prop}", sync_from_settings)

    return cast(BaseWidget, dropdown)


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
                            label="Primary monitor only",
                            subtitle="Hide the bar on secondary displays.",
                            icon="video-display-symbolic",
                            active=bar_settings.show_only_on_primary_monitor,
                            on_change=lambda _, active: bar_settings.set_show_only_on_primary_monitor(active),
                        ),
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
                            label="All workspaces on every monitor",
                            subtitle="Show workspaces even when they belong to another display.",
                            icon="view-grid-symbolic",
                            active=workspace_settings.show_all_ws_on_monitor,
                            on_change=lambda _, active: workspace_settings.set_show_all_ws_on_monitor(active),
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

        keyboard_layout = StringDropdown(
            labels=get_keyboard_layouts(),
            enable_search=True,
            on_change=lambda value: (
                hyprland_settings.set_keyboard_layout(value),
                hyprland_settings.set_keyboard_variant(""),
            ),
            get_current=lambda: hyprland_settings.keyboard_layout,
            settings_obj=hyprland_settings,
            notify_props=["keyboard-layout"],
        )
        keyboard_variant = StringDropdown(
            labels=[],
            enable_search=True,
            on_change=hyprland_settings.set_keyboard_variant,
            get_current=lambda: hyprland_settings.keyboard_variant,
            settings_obj=hyprland_settings,
            notify_props=["keyboard-layout", "keyboard-variant"],
            repopulate=lambda: get_keyboard_variants(
                hyprland_settings.keyboard_layout
            ),
        )
        displays = SettingsPage(
            title="Displays",
            description="Configure displays and choose where primary shell surfaces appear.",
            child=[
                SettingsGroup(
                    title="Displays",
                    description="Select the display that owns primary shell surfaces.",
                    child=[
                        Setting(
                            widget=StringDropdown(
                                labels=[monitor.name for monitor in util.hyprland.monitors],
                                on_change=hyprland_settings.set_primary_monitor,
                                get_current=lambda: hyprland_settings.primary_monitor,
                                settings_obj=hyprland_settings,
                                notify_props=["primary-monitor"],
                            ),
                            label="Primary display",
                            subtitle="Notifications and primary-only shell elements appear here.",
                            icon="video-display-symbolic",
                        ),
                        Setting(
                            widget=Widget.Button(
                                child=Widget.Box(
                                    spacing=7,
                                    child=[
                                        Widget.Label(label="Open Displays"),
                                        Widget.Icon(image="go-next-symbolic", pixel_size=14),
                                    ],
                                ),
                                on_click=lambda _: util.shell("nwg-displays"),
                                css_classes=["settings-secondary-button"],
                            ),
                            label="Display arrangement",
                            subtitle="Configure resolution, scale, position and refresh rate.",
                            icon="preferences-desktop-display-symbolic",
                        )
                        if util.has_command("nwg-displays")
                        else None,
                    ],
                ),
            ],
        )

        self._new_wifi_connections = NewWifiConnections()
        self._new_bluetooth_connections = NewBluetoothConnections()
        self._new_wifi_connections_scroll = Widget.Scroll(
            child=self._new_wifi_connections,
            hexpand=True,
            propagate_natural_height=True,
            min_content_height=240,
            max_content_height=440,
            hscrollbar_policy="never",
            vscrollbar_policy="automatic",
        )
        self._new_bluetooth_connections_scroll = Widget.Scroll(
            child=self._new_bluetooth_connections,
            hexpand=True,
            visible=bluetooth_service.bind("setup_mode"),
            propagate_natural_height=True,
            min_content_height=240,
            max_content_height=440,
            hscrollbar_policy="never",
            vscrollbar_policy="automatic",
        )
        wireless = SettingsPage(
            title="Wi-Fi and Bluetooth",
            description="Discover and connect to new wireless networks and devices.",
            child=[
                SettingsGroup(
                    title="Wi-Fi",
                    description="Connect to networks that are not yet saved on this computer.",
                    child=[
                        SwitchWithLabel(
                            label="Wi-Fi",
                            subtitle="Enable wireless networking.",
                            icon="network-wireless-symbolic",
                            active=network_service.wifi.bind("enabled"),
                            on_change=lambda _, active: network_service.wifi.set_enabled(active),
                        ),
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
                        self._new_wifi_connections_scroll,
                    ],
                ),
                SettingsGroup(
                    title="Bluetooth",
                    description="Pair nearby devices that are not yet known to this computer.",
                    child=[
                        SwitchWithLabel(
                            label="Bluetooth",
                            subtitle="Enable the Bluetooth adapter.",
                            icon="bluetooth-symbolic",
                            active=bluetooth_service.bind("powered"),
                            on_change=lambda _, active: bluetooth_service.set_powered(active),
                        ),
                        SwitchWithLabel(
                            label="Pair new devices",
                            subtitle="Make this computer discoverable and scan nearby devices.",
                            icon="list-add-symbolic",
                            active=bluetooth_service.bind("setup_mode"),
                            sensitive=bluetooth_service.bind("powered"),
                            on_change=lambda _, active: bluetooth_service.set_setup_mode(active),
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
                    description="Choose the layout and optional regional variant.",
                    child=[
                        Setting(
                            widget=keyboard_layout,
                            label="Layout",
                            icon="input-keyboard-symbolic",
                        ),
                        Setting(
                            widget=keyboard_variant,
                            label="Variant",
                            subtitle="Leave empty to use the layout default.",
                            icon="input-keyboard-symbolic",
                        ),
                    ],
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

        windows = SettingsPage(
            title="Windows",
            description="Choose how windows are arranged and managed.",
            child=[
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

        page_specs = [
            ("Appearance", "preferences-desktop-wallpaper-symbolic", appearance),
            ("Shell", "preferences-system-symbolic", shell),
            ("Displays", "preferences-desktop-display-symbolic", displays),
            ("Wi-Fi and Bluetooth", "network-wireless-symbolic", wireless),
            ("Devices", "input-keyboard-symbolic", devices),
            ("Windows", "focus-windows-symbolic", windows),
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

        sidebar = Widget.Box(
            vertical=True,
            spacing=4,
            child=[
                Widget.Box(
                    vertical=True,
                    spacing=2,
                    child=[
                        Widget.Label(
                            label=f"Hello {os.environ.get('USER', 'User')}!",
                            halign="start",
                            css_classes=["settings-sidebar-title"],
                        ),
                        Widget.Label(
                            label="Customise the shell here",
                            halign="start",
                            css_classes=["settings-sidebar-subtitle"],
                        ),
                    ],
                    css_classes=["settings-sidebar-heading"],
                ),
                *navigation,
                Widget.Box(vexpand=True),
                Widget.Separator(css_classes=["settings-sidebar-separator"]),
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
