import asyncio
import os
from typing import Any, Callable, Literal
from gi.repository import GLib, Gtk
from ignis.base_widget import BaseWidget
from ignis.widgets import Widget
from util import BindableSettings, JsonSettings
import util
from widgets.Settings.style_settings import style_settings
from widgets.Clock import clock_settings
from widgets.Workspaces import workspace_settings
from widgets.Launcher.currencies import CURRENCY_CODES
from widgets.Launcher.settings import launcher_settings

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
        with open(os.path.expanduser("~/.local/share/ignis/hyprland.conf"), "w") as f:
            f.write(
                f"""
# Ignis generated Hyprland config, do not edit
# Please put manual changes in ~/.config/hypr/hyprland-custom.conf

input {{
    kb_layout = {self.keyboard_layout}
    kb_variant = {self.keyboard_variant}

    sensitivity = {self.pointer_sensitivity}
    accel_profile = {"flat" if not self.acceleration_enabled else "adaptive"}
}}

general {{
    layout = {self.layout_type}
}}
"""
            )

    primary_monitor: str = util.hyprland.monitors[0].name

    def set_primary_monitor(self, value: str) -> None:
        self.primary_monitor = value


hyprland_settings = HyprlandSettings()


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
    def __init__(self, colour: str, wallpaper: str):
        super().__init__(
            style=f"background-color: {colour};",
            css_classes=["settings-suggested-accent-colour"],
            on_click=lambda _: style_settings.set_accent_colour(colour, wallpaper),
        )


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
                on_click=lambda _: asyncio.create_task(on_wallpaper_picked(path)),
                css_classes=["settings-wallpaper"],
            ),
            overlays=[
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
        label_where: Literal["top", "bottom", "left", "right"] = "right",
    ):
        super().__init__(
            child=[
                widget,
                Widget.Label(
                    label=label,
                    css_classes=["settings-widget-label-right"]
                    if label_where == "right"
                    else ["settings-widget-label-bottom"],
                    halign="start",
                    valign="center",
                ),
            ]
            if label_where in ("right", "bottom")
            else [
                Widget.Label(
                    label=label,
                    css_classes=["settings-widget-label-left"]
                    if label_where == "left"
                    else ["settings-widget-label-top"],
                    halign="start",
                    valign="center",
                ),
                widget,
            ],
            halign="start",
            css_classes=["settings-widget-with-label"],
            vertical=label_where in ("top", "bottom"),
        )


class SwitchWithLabel(Setting):
    def __init__(
        self,
        label: str,
        active: bool = True,
        on_change: Callable[[Widget.Switch, bool], Any] = lambda *_: None,
    ):
        switch = Widget.Switch(
            active=active,
            on_change=on_change,
            valign="center",
        )
        super().__init__(
            label=label,
            widget=switch,
        )


class SettingsSection(Widget.Box):
    def __init__(self, title: str, description: str, child: list[BaseWidget | None]):
        desc = Widget.Label(
            css_classes=["settings-description"],
            halign="start",
        )
        desc.set_markup(description)
        super().__init__(
            vertical=True,
            child=[
                Widget.Label(
                    label=title,
                    css_classes=["settings-subtitle"],
                    halign="start",
                ),
                desc,
                *child,
            ],
            css_classes=["settings-section"],
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


def KeyboardVariantDropdown() -> BaseWidget:
    model = Gtk.StringList()
    syncing = False

    dropdown = Gtk.DropDown(
        model=model,
        expression=Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"),
    )
    dropdown.set_hexpand(False)
    dropdown.set_halign(Gtk.Align.START)
    dropdown.set_valign(Gtk.Align.CENTER)
    dropdown.add_css_class("settings-dropdown")
    dropdown.set_enable_search(True)

    def repopulate(variants: list[str]):
        while model.get_n_items() > 0:
            model.remove(0)
        for v in variants:
            model.append(v)

    def on_selected(dd, _):
        nonlocal syncing
        if syncing:
            return
        item = dd.get_selected_item()
        if item is not None:
            hyprland_settings.set_keyboard_variant(item.props.string)

    dropdown.connect("notify::selected-item", on_selected)

    def sync_from_settings(*_):
        nonlocal syncing
        syncing = True

        variants = get_keyboard_variants(hyprland_settings.keyboard_layout)

        repopulate(variants)

        try:
            dropdown.set_selected(variants.index(hyprland_settings.keyboard_variant))
        except ValueError:
            dropdown.set_selected(0)

        syncing = False

    GLib.idle_add(lambda: (sync_from_settings(), False)[1])

    hyprland_settings.connect("notify::keyboard-layout", sync_from_settings)
    hyprland_settings.connect("notify::keyboard-variant", sync_from_settings)

    return dropdown  # type: ignore


def LayoutDropdown() -> BaseWidget:
    labels = [layout.capitalize() for layout in hyprland_layouts]

    model = Gtk.StringList()
    for label in labels:
        model.append(label)

    dropdown = Gtk.DropDown(
        model=model,
        expression=Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"),
    )
    dropdown.set_hexpand(False)
    dropdown.set_halign(Gtk.Align.START)
    dropdown.set_valign(Gtk.Align.CENTER)
    dropdown.add_css_class("settings-dropdown")

    def on_selected(dd, _):
        item = dd.get_selected_item()
        if item:
            hyprland_settings.set_layout_type(item.props.string.lower())

    dropdown.connect("notify::selected-item", on_selected)

    def sync_from_settings(*_):
        try:
            dropdown.set_selected(hyprland_layouts.index(hyprland_settings.layout_type))
        except ValueError:
            pass

    GLib.idle_add(lambda: (sync_from_settings(), False)[1])

    hyprland_settings.connect("notify::layout-type", sync_from_settings)

    return dropdown  # type: ignore


def PrimaryMonitorDropdown() -> BaseWidget:
    labels = [m.name for m in util.hyprland.monitors]

    model = Gtk.StringList()
    for label in labels:
        model.append(label)

    dropdown = Gtk.DropDown(
        model=model,
        expression=Gtk.PropertyExpression.new(Gtk.StringObject, None, "string"),
    )

    dropdown.set_hexpand(False)
    dropdown.set_halign(Gtk.Align.START)
    dropdown.set_valign(Gtk.Align.CENTER)
    dropdown.add_css_class("settings-dropdown")

    def on_selected(dd, _):
        item = dd.get_selected_item()
        if item:
            hyprland_settings.set_primary_monitor(item.props.string)

    dropdown.connect("notify::selected-item", on_selected)

    def sync_from_settings(*_):
        try:
            dropdown.set_selected(labels.index(hyprland_settings.primary_monitor))
        except ValueError:
            pass

    GLib.idle_add(lambda: (sync_from_settings(), False)[1])

    hyprland_settings.connect("notify::primary-monitor", sync_from_settings)

    return dropdown  # type: ignore


def PreferredCurrencyDropdown() -> BaseWidget:
    labels = CURRENCY_CODES

    model = Gtk.StringList()
    for label in labels:
        model.append(label)

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
        if item:
            launcher_settings.set_preferred_currency(item.props.string)

    dropdown.connect("notify::selected-item", on_selected)

    def sync_from_settings(*_):
        try:
            dropdown.set_selected(labels.index(launcher_settings.preferred_currency))
        except ValueError:
            pass

    launcher_settings.connect("notify::preferred-currency", sync_from_settings)
    sync_from_settings()

    return dropdown  # type: ignore


class SettingsWindow(Widget.RegularWindow):
    def __init__(self):
        self.suggested_accent_colours = Widget.Box(
            css_classes=["settings-suggested-accent-colours"]
        )
        self.wallpapers_box = Widget.Box(
            vexpand=True,
            child=style_settings.bind_many(
                ["wallpaper", "addedwallpapers"],
                lambda *_: [
                    WallpaperButton(
                        p,
                        self.on_wallpaper_picked,
                        self.on_wallpaper_removed,
                        p == style_settings.wallpaper,
                    )
                    for p in style_settings.get_wallpapers()
                ],
            ),
            css_classes=["settings-wallpapers-box"],
        )
        self.wallpapers_scroll = Widget.Scroll(
            child=self.wallpapers_box,
            css_classes=["settings-wallpapers-scroll"],
        )

        self.color_chooser = Gtk.ColorDialog()

        asyncio.create_task(
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
            on_change=lambda _: style_settings.set_post_accent_change_cmd(self.post_accent_change_entry.get_text())
        )
        self.post_accent_change_entry.set_text(style_settings.post_accent_change_cmd)

        box = Widget.Box(
            vertical=True,
            vexpand=True,
            child=[
                SettingsSection(
                    title="Wallpaper",
                    description="Select a wallpaper for your desktop or add your own images to the library.",
                    child=[
                        self.wallpapers_scroll,
                        Widget.Box(
                            halign="start",
                            child=[
                                Widget.Button(
                                    label="Add new",
                                    on_click=lambda _: asyncio.create_task(
                                        add_wallpaper_dialog.open_dialog()
                                    ),
                                    css_classes=["settings-wallpaper-button"],
                                ),
                            ],
                        ),
                    ],
                ),
                SettingsSection(
                    title="Accent colour",
                    description="Choose the system accent colour, either suggested from your wallpaper or set manually.",
                    child=[
                        self.suggested_accent_colours,
                        Widget.Box(
                            child=[
                                Widget.Button(
                                    halign="start",
                                    label="Set custom",
                                    on_click=lambda _: self.color_chooser.choose_rgba(
                                        parent=None,
                                        cancellable=None,
                                        callback=self.on_color_chosen,
                                    ),  # type: ignore
                                    css_classes=["change-accent-colour-button"],
                                ),
                                Widget.Button(
                                    halign="start",
                                    label="Restore default",
                                    on_click=lambda _: style_settings.restore_accent_colour(
                                        style_settings.wallpaper
                                    ),
                                    css_classes=["change-accent-colour-button"],
                                ),
                            ],
                        ),
                        Setting(
                            widget=self.post_accent_change_entry,
                            label="Post accent colour change command",
                        ),
                    ],
                ),
                SettingsSection(
                    title="Clock",
                    description="Control the clock format and which details are shown in the top bar and on the lock screen.",
                    child=[
                        Widget.Box(
                            vertical=True,
                            child=[
                                SwitchWithLabel(
                                    label="Use 24-hour format",
                                    active=clock_settings.use_24h,
                                    on_change=lambda _,
                                    active: clock_settings.set_use_24h(active),
                                ),
                                SwitchWithLabel(
                                    label="Show day of week",
                                    active=clock_settings.show_dow,
                                    on_change=lambda _,
                                    active: clock_settings.set_show_dow(active),
                                ),
                                SwitchWithLabel(
                                    label="Show seconds",
                                    active=clock_settings.show_seconds,
                                    on_change=lambda _,
                                    active: clock_settings.set_show_seconds(active),
                                ),
                            ],
                        )
                    ],
                ),
                SettingsSection(
                    title="Workspaces",
                    description="Decide how workspaces are displayed across monitors in the top bar.",
                    child=[
                        SwitchWithLabel(
                            label="Show all workspaces on each monitor",
                            active=workspace_settings.show_all_ws_on_monitor,
                            on_change=lambda _,
                            active: workspace_settings.set_show_all_ws_on_monitor(
                                active
                            ),
                        )
                    ],
                ),
                SettingsSection(
                    title="Launcher",
                    description="Adjust how the launcher behaves and configure its built-in features.",
                    child=[
                        Setting(
                            widget=PreferredCurrencyDropdown(),
                            label="Preferred target currency for conversion",
                        ),
                    ],
                ),
                SettingsSection(
                    title="Display settings",
                    description="Manage monitor configuration, primary display selection, and related display options.",
                    child=[
                        Setting(
                            Widget.Button(
                                child=Widget.Label(label="Launch nwg-displays"),
                                on_click=lambda _: util.shell("nwg-displays"),
                            )
                        )
                        if util.has_command("nwg-displays")
                        else None,
                        Setting(
                            widget=PrimaryMonitorDropdown(),
                            label="Primary monitor (does not affect Hyprland, only the shell)",
                        ),
                    ],
                ),
                SettingsSection(
                    title="Keyboard layout",
                    description="Select the keyboard layout and optional variant used by Hyprland.\nLeave variant empty to use the default for the selected layout.",
                    child=[
                        Setting(
                            widget=Widget.Box(
                                child=[
                                    KeyboardLayoutDropdown(),
                                    KeyboardVariantDropdown(),
                                ],
                                spacing=8,
                            ),
                        ),
                    ],
                ),
                SettingsSection(
                    title="Mouse sensitivity",
                    description="Adjust mouse sensitivity and acceleration in Hyprland.",
                    child=[
                        Setting(
                            Widget.Scale(
                                min=-1.0,
                                max=1.0,
                                step=0.1,
                                value=hyprland_settings.bind("pointer_sensitivity"),
                                on_change=lambda s: hyprland_settings.set_pointer_sensitivity(
                                    s.get_value()
                                ),
                                css_classes=["settings-pointer-speed-scale"],
                            )
                        ),
                        SwitchWithLabel(
                            label="Pointer acceleration",
                            active=hyprland_settings.bind("acceleration_enabled"),  # type: ignore
                            on_change=lambda _,
                            active: hyprland_settings.set_acceleration_enabled(active),
                        ),
                    ],  # type: ignore
                ),
                SettingsSection(
                    title="Tiling layout",
                    description="""Select the window tiling algorithm used by Hyprland and how windows are arranged.
Learn more about each layout <a href=\"https://wiki.hypr.land/Configuring/Dwindle-Layout/\">here</a> and <a href=\"https://wiki.hypr.land/Configuring/Master-Layout/\">here</a>.""",
                    child=[Setting(LayoutDropdown())],
                ),
            ],
            css_classes=["settings"],
        )

        lc = box.get_last_child()
        if lc is not None:
            lc.add_css_class("last")

        super().__init__(
            child=Widget.Scroll(
                child=box,
            ),
            namespace="ignis_settings",
            css_classes=["window"],
            visible=False,
            hide_on_close=True,
        )

    def on_color_chosen(self, source, result):
        try:
            rgba = source.choose_rgba_finish(result)
            style_settings.handle_color_chosen(rgba, style_settings.wallpaper)
        except:
            return

    async def update_suggested_accent_colours(self, path: str):
        top_colours = await style_settings.get_cached_top_colours(path)
        self.suggested_accent_colours.set_child(
            [AccentColourButton(colour=c, wallpaper=path) for c in top_colours]
        )

    async def on_wallpaper_picked(self, file):
        await style_settings.pick_wallpaper(file)
        await self.update_suggested_accent_colours(file)
        self.wallpapers_scroll.get_vadjustment().set_value(0)

    def on_wallpaper_removed(self, path):
        style_settings.remove_wallpaper(path)
