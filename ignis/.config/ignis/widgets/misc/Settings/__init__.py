import asyncio
from gi.repository import Gtk  # type: ignore
from ignis.widgets import Widget
from widgets.misc.Settings.style_manager import StyleManager

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
                        Widget.Box(
                            vertical=True,
                            child=[
                                Widget.Label(
                                    label="Wallpaper",
                                    css_classes=["settings-subtitle"],
                                    halign="start",
                                ),
                                Widget.Label(
                                    label="Change the wallpaper of the desktop by clicking on one of them.",
                                    css_classes=["settings-description"],
                                    halign="start",
                                ),
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
                                            on_click=lambda _: refresh_wallpapers(),
                                            css_classes=["settings-wallpaper-button"],
                                            halign="start",
                                        ),
                                    ],
                                ),
                            ],
                            css_classes=["settings-section"],
                        ),
                        Widget.Box(
                            vertical=True,
                            child=[
                                Widget.Label(
                                    label="Accent Colour",
                                    css_classes=["settings-subtitle"],
                                    halign="start",
                                ),
                                Widget.Label(
                                    label="Pick one of the suggested colours based on your wallpaper:",
                                    css_classes=["settings-description"],
                                    halign="start",
                                ),
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
                                            on_click=lambda _: color_chooser.choose_rgba(parent=None, cancellable=None, callback=self.on_color_chosen), # type: ignore
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
                            css_classes=["settings-section"],
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
