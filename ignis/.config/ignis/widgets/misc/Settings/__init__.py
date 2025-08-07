import asyncio
from ignis.widgets import Widget
import os
import utils
from gi.repository import Gtk # type: ignore

import utils

def AccentColourPicker(colour: str):
    return Widget.Button(
        style=f"background-color: {colour};",
        css_classes=["settings-suggested-accent-colour"],
        on_click=lambda _: set_accent_colour(colour),
    )

def set_accent_colour(colour: str):
    print(colour)
    with open(os.path.expanduser("~/.config/ignis/accent.scss"), "w") as f:
        f.write(f"$accent: {colour};\n")

def Settings():
    wallpaper_pic = Widget.Picture(
        image=os.path.expanduser("~/.wallpapers/.wallpaper"),
        content_fit="scale_down",
        height=(wallpaper_size := 196),
        width=wallpaper_size * 16 // 9,
        css_classes=["settings-wallpaper-image"],
    )
    
    suggested_accent_colours = Widget.Box(
        css_classes=["settings-suggested-accent-colours"]
    )

    color_chooser = Gtk.ColorDialog()
    def on_color_chosen(source, result):
        try:
            rgba = source.choose_rgba_finish(result)
            hex_colour = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
            set_accent_colour(hex_colour)
        except:
            return

    async def set_suggested_accent_colours(path: str):
        top_colours = await utils.get_top_colours(path)

        suggested_accent_colours.child = [ # type: ignore
            AccentColourPicker(
                colour=colour,
            ) for colour in top_colours
        ]

    asyncio.create_task(set_suggested_accent_colours(os.path.expanduser("~/.wallpapers/.wallpaper")))

    def on_wallpaper_picked(_, file):
        utils.run_cmd(f"~/.wallpapers/switch {file.get_path()}")
        wallpaper_pic.set_image(file.get_path())
        asyncio.create_task(set_suggested_accent_colours(file.get_path()))

    pick_wallpaper = Widget.FileDialog(
        initial_path=os.path.expanduser("~/.wallpapers"),
        on_file_set=on_wallpaper_picked,
        select_folder=False,
        filters=[
            Widget.FileFilter(
                mime_types=["image/jpeg", "image/png", "image/webp"],
                default=True,
                name="Image"
            )
        ]
    )

    return Widget.RegularWindow(
        child=Widget.Scroll(
            child=Widget.Box(
                vertical=True,
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
                                label="Change the wallpaper of the desktop.",
                                css_classes=["settings-description"],
                                halign="start",
                            ),
                            Widget.Button(
                                child=wallpaper_pic,
                                css_classes=["settings-wallpaper"],
                                on_click=lambda _: asyncio.create_task(pick_wallpaper.open_dialog()),
                                halign="start",
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
                            suggested_accent_colours,
                            Widget.Label(
                                label="Or:",
                                css_classes=["settings-description"],
                                halign="start",
                            ),
                            Widget.Button(
                                halign="start",
                                label="Set custom accent colour",
                                on_click=lambda _: color_chooser.choose_rgba(parent=None, cancellable=None, callback=on_color_chosen),
                                css_classes=["change-accent-colour-button"],
                            ),
                        ],
                        css_classes=["settings-section"],
                    ),
                ],
                css_classes=["settings"],
            ),
        ),
        namespace="ignis_settings",
        css_classes=["runset"],
        visible=False,
        hide_on_close=True,
    )
