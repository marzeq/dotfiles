import asyncio
from typing import Any, Callable
from gi.repository import Gtk  # type: ignore
from ignis.widgets import Widget
from widgets.misc.Settings.style_manager import StyleManager
from widgets.bar.Clock import clock_settings

sm = StyleManager.instance()


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
        css_classes: list[str] = []
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
    def __init__(self, title: str, description: str, child: list[Widget]):
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


class SettingsWindow(Widget.RegularWindow):
    def __init__(self):
        self.suggested_accent_colours = Widget.Box(css_classes=["settings-suggested-accent-colours"])
        self.wallpapers_box = Widget.Box(child=[])
        self.color_chooser = Gtk.ColorDialog()

        asyncio.create_task(self.update_suggested_accent_colours(sm.wallpaper_symlink))
        self.refresh_wallpapers()

        add_wallpaper_dialog = Widget.FileDialog(
            on_file_set=lambda _, file: (sm.add_wallpaper(file), self.refresh_wallpapers()),
            select_folder=False,
            filters=[Widget.FileFilter(mime_types=["image/jpeg", "image/png", "image/webp"],
                                       default=True, name="Image")]
        )

        super().__init__(
            child=Widget.Scroll(
                child=Widget.Box(
                    vertical=True,
                    vexpand=True,
                    child=[
                        SettingsSection(
                            title="Wallpaper",
                            description="Change the wallpaper of the desktop by clicking on one of them.",
                            child=[
                                Widget.Scroll(
                                    child=self.wallpapers_box,
                                    css_classes=["settings-wallpapers-scroll"],
                                ),
                                Widget.Box(
                                    halign="start",
                                    child=[
                                        Widget.Button(
                                            label="Add a new wallpaper",
                                            on_click=lambda _: asyncio.create_task(add_wallpaper_dialog.open_dialog()),
                                            css_classes=["settings-wallpaper-button"],
                                        ),
                                        Widget.Button(
                                            label="Refresh wallpapers",
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
                            description="Change the accent colour of the desktop.",
                            child=[
                                self.suggested_accent_colours,
                                Widget.Label(
                                    label="Or:",
                                    css_classes=["settings-description"],
                                    halign="start",
                                ),
                                Widget.Box(
                                    child=[
                                        Widget.Button(
                                            halign="start",
                                            label="Set custom accent colour",
                                            on_click=lambda _: self.color_chooser.choose_rgba(parent=None, cancellable=None, callback=self.on_color_chosen), # type: ignore
                                            css_classes=["change-accent-colour-button"],
                                        ),
                                        Widget.Button(
                                            halign="start",
                                            label="Restore default accent colour",
                                            on_click=lambda _: sm.restore_accent_colour(sm.wallpaper_symlink),
                                            css_classes=["change-accent-colour-button"],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        SettingsSection(
                            title="Clock",
                            description="Customize the clock in the top bar",
                            child=[
                                Widget.Box(
                                    vertical=True,
                                    child=[
                                        SwitchWithLabel(
                                            label="Use 24-hour format",
                                            active=clock_settings.use_24h,
                                            on_change=lambda _, active: clock_settings.set_use_24h(active),
                                            css_classes=["settings-clock-switch"]
                                        ),
                                        SwitchWithLabel(
                                            label="Show day of week",
                                            active=clock_settings.show_dow,
                                            on_change=lambda _, active: clock_settings.set_show_dow(active),
                                            css_classes=["settings-clock-switch"]
                                        ),
                                        SwitchWithLabel(
                                            label="Show seconds",
                                            active=clock_settings.show_seconds,
                                            on_change=lambda _, active: clock_settings.set_show_seconds(active),
                                            css_classes=["settings-clock-switch"]
                                        )
                                    ],
                                )
                            ],
                        ),
                    ],
                    css_classes=["settings"],
                ),
            ),
            namespace="ignis_settings",
            css_classes=["window"],
            visible=sm.has_lockfile(),
            hide_on_close=True,
        )

        sm.remove_lockfile()
    
    def on_color_chosen(self, source, result):
        try:
            rgba = source.choose_rgba_finish(result)
            sm.handle_color_chosen(rgba, sm.wallpaper_symlink)
        except:
            return

    async def update_suggested_accent_colours(self, path: str):
        top_colours = await sm.get_cached_top_colours(path)
        self.suggested_accent_colours.child = [ # type: ignore
            AccentColourButton(colour=c, wallpaper=path) for c in top_colours
        ]

    def refresh_wallpapers(self):
        self.wallpapers_box.child = [ # type: ignore
            WallpaperButton(p, self.on_wallpaper_picked) for p in sm.get_wallpapers()
        ]

    async def on_wallpaper_picked(self, file):
        await sm.pick_wallpaper(file, self.refresh_wallpapers)
        await self.update_suggested_accent_colours(file)
