import asyncio
import os
from typing import Any, Callable, Literal
from gi.repository import GLib, Gtk
from ignis.base_widget import BaseWidget
from ignis.widgets import Widget
from util import BindableSettings, JsonSettings
from widgets.Settings.style_manager import StyleManager
from widgets.Clock import clock_settings
from widgets.Workspaces import workspace_settings

sm = StyleManager.instance()

HyprlandLayout = Literal["master"] | Literal["dwindle"]
hyprland_layouts: list[HyprlandLayout] = ["master", "dwindle"]

@JsonSettings("hyprland")
class HyprlandSettings(BindableSettings):
    keyboard_layout: str = "us"
    def set_keyboard_layout(self, value: str) -> None:
        self.keyboard_layout = value

    layout_type: HyprlandLayout = "master"
    def set_layout_type(self, value: HyprlandLayout) -> None:
        self.layout_type = value

    
    def sync(self) -> None:
        with open(
            os.path.expanduser("~/.local/share/ignis/hyprland.conf"), "w"
        ) as f:
            f.write(
                f"""
# Ignis generated Hyprland config, do not edit
# Please put manual changes in ~/.config/hypr/hyprland-custom.conf

input {{
    kb_layout = {self.keyboard_layout}
}}

general {{
    layout = {self.layout_type}
}}
""")

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
                    if parts:
                        layouts.append(parts[0])
    return layouts


class AccentColourButton(Widget.Button):
    def __init__(self, colour: str, wallpaper: str):
        super().__init__(
            style=f"background-color: {colour};",
            css_classes=["settings-suggested-accent-colour"],
            on_click=lambda _: sm.set_accent_colour(colour, wallpaper),
        )


class WallpaperButton(Widget.Button):
    def __init__(self, path: str, on_wallpaper_picked):
        wallpaper_size = 196
        super().__init__(
            child=Widget.Picture(
                image=path,
                content_fit="scale_down",
                height=wallpaper_size,
                width=wallpaper_size * 16 // 9,
                css_classes=["settings-wallpaper-image"],
            ),
            css_classes=["settings-wallpaper"],
            on_click=lambda _: asyncio.create_task(on_wallpaper_picked(path)),
            halign="start",
        )


class SwitchWithLabel(Widget.Box):
    def __init__(
        self,
        label: str,
        active: bool = True,
        on_change: Callable[[Widget.Switch, bool], Any] = lambda *_: None,
        css_classes: list[str] = [],
    ):
        super().__init__(
            child=[
                Widget.Switch(
                    active=active,
                    on_change=on_change,
                    valign="center",
                ),
                Widget.Label(
                    label=label,
                    css_classes=["settings-switch-label"],
                    halign="start",
                    valign="center",
                ),
            ],
            halign="start",
            css_classes=css_classes,
        )


class SettingsSection(Widget.Box):
    def __init__(self, title: str, description: str, child: list[BaseWidget]):
        super().__init__(
            vertical=True,
            child=[
                Widget.Label(
                    label=title,
                    css_classes=["settings-subtitle"],
                    halign="start",
                ),
                Widget.Label(
                    label=description,
                    css_classes=["settings-description"],
                    halign="start",
                ),
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
        expression=Gtk.PropertyExpression.new(
            Gtk.StringObject, None, "string"
        ),
    )
    dropdown.set_hexpand(False)
    dropdown.set_halign(Gtk.Align.START)
    dropdown.set_valign(Gtk.Align.CENTER)
    dropdown.add_css_class("settings-dropdown")
    dropdown.set_enable_search(True)

    def on_selected(dd, _):
        item = dd.get_selected_item()
        if item:
            hyprland_settings.set_keyboard_layout(item.props.string)

    dropdown.connect("notify::selected-item", on_selected)

    def sync_from_settings(*_):
        try:
            dropdown.set_selected(
                layouts.index(hyprland_settings.keyboard_layout)
            )
        except ValueError:
            pass

    GLib.idle_add(lambda: (sync_from_settings(), False)[1])

    hyprland_settings.bind("keyboard_layout", sync_from_settings)

    return dropdown # type: ignore


def LayoutDropdown() -> BaseWidget:
    labels = [layout.capitalize() for layout in hyprland_layouts]

    model = Gtk.StringList()
    for label in labels:
        model.append(label)

    dropdown = Gtk.DropDown(
        model=model,
        expression=Gtk.PropertyExpression.new(
            Gtk.StringObject, None, "string"
        ),
    )
    dropdown.set_hexpand(False)
    dropdown.set_halign(Gtk.Align.START)
    dropdown.set_valign(Gtk.Align.CENTER)
    dropdown.add_css_class("settings-dropdown")

    def on_selected(dd, _):
        item = dd.get_selected_item()
        if item:
            hyprland_settings.set_layout_type(
                item.props.string.lower()
            )

    dropdown.connect("notify::selected-item", on_selected)

    def sync_from_settings(*_):
        try:
            dropdown.set_selected(
                hyprland_layouts.index(
                    hyprland_settings.layout_type
                )
            )
        except ValueError:
            pass

    GLib.idle_add(lambda: (sync_from_settings(), False)[1])

    hyprland_settings.bind("layout_type", sync_from_settings)

    return dropdown # type: ignore

class SettingsWindow(Widget.RegularWindow):
    def __init__(self):
        self.suggested_accent_colours = Widget.Box(
            css_classes=["settings-suggested-accent-colours"]
        )
        self.wallpapers_box = Widget.Box(child=[])
        self.color_chooser = Gtk.ColorDialog()

        asyncio.create_task(self.update_suggested_accent_colours(sm.wallpaper_symlink))
        self.refresh_wallpapers()

        add_wallpaper_dialog = Widget.FileDialog(
            on_file_set=lambda _, file: (
                sm.add_wallpaper(file),
                self.refresh_wallpapers(),
            ),
            select_folder=False,
            filters=[
                Widget.FileFilter(
                    mime_types=["image/jpeg", "image/png", "image/webp"],
                    default=True,
                    name="Image",
                )
            ],
        )

        self.wallpapers_scroll = Widget.Scroll(
            child=self.wallpapers_box,
            css_classes=["settings-wallpapers-scroll"],
        )

        super().__init__(
            child=Widget.Scroll(
                child=Widget.Box(
                    vertical=True,
                    vexpand=True,
                    child=[
                        SettingsSection(
                            title="Wallpaper",
                            description="Select from one of the available wallpapers or add a new one",
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
                                        Widget.Button(
                                            label="Refresh",
                                            on_click=lambda _: self.refresh_wallpapers(),
                                            css_classes=["settings-wallpaper-button"],
                                            halign="start",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        SettingsSection(
                            title="Accent Colour",
                            description="Pick an accent colour to match your wallpaper\nYour colour may be slightly adjusted for legibility purposes",
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
                                            on_click=lambda _: sm.restore_accent_colour(
                                                sm.wallpaper_symlink
                                            ),
                                            css_classes=["change-accent-colour-button"],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        SettingsSection(
                            title="Clock",
                            description="Customise how the clock behaves in the top bar and lock screen",
                            child=[
                                Widget.Box(
                                    vertical=True,
                                    child=[
                                        SwitchWithLabel(
                                            label="Use 24-hour format",
                                            active=clock_settings.use_24h,
                                            on_change=lambda _,
                                            active: clock_settings.set_use_24h(active),
                                            css_classes=["settings-switch"],
                                        ),
                                        SwitchWithLabel(
                                            label="Show day of week",
                                            active=clock_settings.show_dow,
                                            on_change=lambda _,
                                            active: clock_settings.set_show_dow(active),
                                            css_classes=["settings-switch"],
                                        ),
                                        SwitchWithLabel(
                                            label="Show seconds",
                                            active=clock_settings.show_seconds,
                                            on_change=lambda _,
                                            active: clock_settings.set_show_seconds(
                                                active
                                            ),
                                            css_classes=["settings-switch"],
                                        ),
                                    ],
                                )
                            ],
                        ),
                        SettingsSection(
                            title="Workspaces",
                            description="Change the behaviour of the workspaces widget in the top bar",
                            child=[
                                SwitchWithLabel(
                                    label="Show all workspaces on each monitor",
                                    active=workspace_settings.show_all_ws_on_monitor,
                                    on_change=lambda _,
                                    active: workspace_settings.set_show_all_ws_on_monitor(
                                        active
                                    ),
                                    css_classes=["settings-switch"],
                                )
                            ],
                        ),
                        SettingsSection(
                            title="Keyboard layout",
                            description="Change the keyboard layout used by Hyprland",
                            child=[KeyboardLayoutDropdown()],
                        ),
                        SettingsSection(
                            title="Layout type",
                            description="Tiling mode/layout used by Hyprland\nDwindle - windows get smaller as more are added\nMaster - one large window with others tiled alongside",
                            child=[LayoutDropdown()],
                        ),
                    ],
                    css_classes=["settings"],
                ),
            ),
            namespace="ignis_settings",
            css_classes=["window"],
            visible=False,
            hide_on_close=True,
        )

    def on_color_chosen(self, source, result):
        try:
            rgba = source.choose_rgba_finish(result)
            sm.handle_color_chosen(rgba, sm.wallpaper_symlink)
        except:
            return

    async def update_suggested_accent_colours(self, path: str):
        top_colours = await sm.get_cached_top_colours(path)
        self.suggested_accent_colours.child = [  # type: ignore
            AccentColourButton(colour=c, wallpaper=path) for c in top_colours
        ]

    def refresh_wallpapers(self):
        self.wallpapers_box.child = [  # type: ignore
            WallpaperButton(p, self.on_wallpaper_picked) for p in sm.get_wallpapers()
        ]

    async def on_wallpaper_picked(self, file):
        await sm.pick_wallpaper(file, self.refresh_wallpapers)
        await self.update_suggested_accent_colours(file)
        self.wallpapers_scroll.get_vadjustment().set_value(0)
