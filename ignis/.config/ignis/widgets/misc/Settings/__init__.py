import asyncio
from typing import Callable
from ignis.widgets import Widget
import os
import shutil
import subprocess
import util
from gi.repository import Gtk # type: ignore

import util

def AccentColourPicker(colour: str):
    return Widget.Button(
        style=f"background-color: {colour};",
        css_classes=["settings-suggested-accent-colour"],
        on_click=lambda _: set_accent_colour(colour),
    )

def set_accent_colour(colour: str):
    with open(os.path.expanduser("~/.local/share/ignis/accent.scss"), "w") as f:
        f.write(f"$accent: {colour};\n")

    util.run_cmd(f"{util.root_dir}/scripts/change_accent.sh \"{colour}\"")

def restore_accent_colour():
    with open(os.path.expanduser("~/.local/share/ignis/accent.scss"), "w") as f:
        f.write("\n")

    util.run_cmd(f"{util.root_dir}/scripts/restore_accent.sh") # type: ignore

wallpapers_dir = os.path.expanduser("~/.wallpapers")
wallpaper_path = os.path.join(wallpapers_dir, ".wallpaper")


def set_wallpaper(selected_path):
    selected_abs = os.path.realpath(os.path.expanduser(selected_path))

    if not os.path.isfile(selected_abs):
        raise FileNotFoundError(f"File not found: {selected_abs}")

    dest_path = os.path.join(wallpapers_dir, os.path.basename(selected_abs))

    if not selected_abs.startswith(wallpapers_dir + os.sep):
        if not os.path.exists(dest_path) or not os.path.samefile(selected_abs, dest_path):
            shutil.copy2(selected_abs, dest_path)
        selected_abs = dest_path

    try:
        os.unlink(wallpaper_path)
    except FileNotFoundError:
        pass

    rel_path = os.path.relpath(selected_abs, wallpapers_dir)
    os.symlink(rel_path, wallpaper_path)

    subprocess.run(["pkill", "hyprpaper"], check=False)
    subprocess.run(["hyprctl", "dispatch", "exec", "hyprpaper"], check=False)

def add_wallpaper(selected_rel):
    if not os.path.isfile(selected_rel):
        raise FileNotFoundError(f"File not found: {selected_rel}")

    selected_abs = os.path.realpath(os.path.expanduser(selected_rel))
    if selected_abs.startswith(wallpapers_dir + os.sep):
        return

    dest_path = os.path.join(wallpapers_dir, os.path.basename(selected_abs))
    if not os.path.exists(dest_path) or not os.path.samefile(selected_abs, dest_path):
        shutil.copy2(selected_abs, dest_path)

def Wallpaper(path: str, on_wallpaper_picked: Callable[[str], None]):
    return Widget.Button(
        child=Widget.Picture(
            image=path,
            content_fit="scale_down",
            height=(wallpaper_size := 196),
            width=wallpaper_size * 16 // 9,
            css_classes=["settings-wallpaper-image"],
        ),
        css_classes=["settings-wallpaper"],
        on_click=lambda _: on_wallpaper_picked(path),
        halign="start",
    )

def get_wallpapers():
    wallpapers = []

    if os.path.exists(wallpaper_path):
        wallpapers.append(wallpaper_path)

    current_wallpaper = None
    if os.path.islink(wallpaper_path):
        target_abs = os.path.realpath(wallpaper_path)
        if target_abs.startswith(wallpapers_dir):
            current_wallpaper = os.path.relpath(target_abs, wallpapers_dir)
        else:
            current_wallpaper = os.path.basename(target_abs)

    for file in os.listdir(wallpapers_dir):
        if not file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            continue
        if file != current_wallpaper:
            wallpapers.append(os.path.join(wallpapers_dir, file))

    return wallpapers

def Settings():
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
        top_colours = await util.get_top_colours(path)

        suggested_accent_colours.child = [ # type: ignore
            AccentColourPicker(
                colour=colour,
            ) for colour in top_colours
        ]

    asyncio.create_task(set_suggested_accent_colours(wallpaper_path))

    wallpapers = Widget.Box(
        child=[]
    )

    def refresh_wallpapers():
        wallpapers.child = [ # type: ignore
            Wallpaper(path, on_wallpaper_picked) for path in get_wallpapers()
        ]

    def on_wallpaper_picked(file):
        set_wallpaper(file)
        asyncio.create_task(set_suggested_accent_colours(file))

        refresh_wallpapers()

    refresh_wallpapers()

    add_wallpaper_dialog = Widget.FileDialog(
        on_file_set=lambda _, file: add_wallpaper(file) or refresh_wallpapers(),
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
                                child=wallpapers,
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
                            suggested_accent_colours,
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
                                        on_click=lambda _: color_chooser.choose_rgba(parent=None, cancellable=None, callback=on_color_chosen),
                                        css_classes=["change-accent-colour-button"],
                                    ),
                                    Widget.Button(
                                        halign="start",
                                        label="Restore default accent colour",
                                        on_click=lambda _: restore_accent_colour(),
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
        visible=False,
        hide_on_close=True,
    )
