import subprocess
import os
from typing import Callable

from ignis.app import IgnisApp
from ignis.services.hyprland.service import HyprlandService
from ignis.utils import Utils

from PIL import Image
from ignis.widgets import Widget
import numpy as np
from sklearn.cluster import KMeans

app: IgnisApp
def get_app():
    global app
    try:
        app = IgnisApp.get_default()
    except:
        pass

    return app
app = get_app()
        
hyprland = HyprlandService.get_default()

root_dir = Utils.get_current_dir() # type: ignore

def active_monitor() -> int:
    return hyprland.active_workspace.monitor_id

def run_cmd(cmd: str) -> None:
    subprocess.Popen(
        ["/bin/bash", "-c", cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setpgrp
    )

def run_cmd_and_run(cmd: str, runnable: Callable) -> None:
    runnable()
    run_cmd(cmd)

def run_cmd_and_run_delayed(cmd: str, runnable: Callable, delay: int) -> None:
    runnable()
    Utils.Timeout(delay, lambda *_: run_cmd(cmd))

async def get_top_colours(image_path, num_colours=50, top_n=10, min_distance=50):
    def rgb_distance(c1, c2):
        return np.linalg.norm(np.array(c1) - np.array(c2))

    img = Image.open(image_path).convert("RGB")
    img = img.resize((200, 200))
    pixels = list(img.getdata())

    kmeans = KMeans(n_clusters=num_colours, random_state=0)
    kmeans.fit(pixels)
    colours = kmeans.cluster_centers_

    def saturation(rgb):
        r, g, b = [x / 255.0 for x in rgb]
        mx = max(r, g, b)
        mn = min(r, g, b)
        return 0 if mx == 0 else (mx - mn) / mx

    sorted_colours = sorted(colours, key=saturation, reverse=True)

    diverse_colours = []
    for c in sorted_colours:
        if all(rgb_distance(c, dc) >= min_distance for dc in diverse_colours):
            diverse_colours.append(c)
        if len(diverse_colours) >= top_n:
            break

    hex_colours = [
        f'#{int(c[0]):02X}{int(c[1]):02X}{int(c[2]):02X}'
        for c in diverse_colours
    ]

    return hex_colours


# Popup management

popup_anim_speed = 100

curr_popup = None
curr_popup_monitor = None

popup_triggers_by_name: dict[str, Widget.Box] = {}
def set_active(name: str, monitor: int, active: bool):
    popup_name = f"{name}_{monitor}"
    box = popup_triggers_by_name.get(popup_name)
    if box is None:
        return
    if active:
        box.css_classes = box.css_classes + ["active"]
    else:
        box.css_classes = [clas for clas in box.css_classes if clas != "active"]

def set_popup(name: str) -> None:
    global curr_popup, curr_popup_monitor
    curr_popup = name
    curr_popup_monitor = active_monitor()
    set_active(curr_popup, curr_popup_monitor, True)

def reset_popup() -> None:
    global curr_popup, curr_popup_monitor
    if curr_popup is not None and curr_popup_monitor is not None:
        set_active(curr_popup, curr_popup_monitor, False)
    curr_popup = None
    curr_popup_monitor = None

def handle_popup_clicked(name: str) -> None:
    global curr_popup, curr_popup_monitor

    clear_popupers()
    if curr_popup == name:
        if curr_popup_monitor is None:
            app.open_window(f"{name}_{active_monitor()}")
            set_popup(name)
            open_popupers()
        elif curr_popup_monitor == active_monitor():
            close_curr_popup()
        else:
            close_curr_popup()
            app.open_window(f"{name}_{active_monitor()}")
            set_popup(name)
            open_popupers()
    else:
        close_curr_popup()
        app.open_window(f"{name}_{active_monitor()}")
        set_popup(name)
        open_popupers()

def close_curr_popup() -> None:
    global curr_popup, curr_popup_monitor
    if curr_popup is not None:
        app.close_window(f"{curr_popup}_{curr_popup_monitor}")
        clear_popupers()
        reset_popup()

def clear_popupers():
    for i in range(Utils.get_n_monitors()): # type: ignore
        if curr_popup_monitor is None or i != curr_popup_monitor:
            app.close_window(f"ignis_close_popuper_{i}")

def open_popupers():
    for i in range(Utils.get_n_monitors()): # type: ignore
        if i != active_monitor():
            app.open_window(f"ignis_close_popuper_{i}")



from gi.repository import Gio # type: ignore

DBUS_DIR = os.path.dirname(__file__) + "/services/dbus"

def load_interface_xml(
    interface_name: str | None = None, path: str | None = None, xml: str | None = None
) -> Gio.DBusInterfaceInfo:
    """
    Load interface info from XML.
    If you want to load interface info from the path or XML string, you need to provide ``path`` and ``xml`` as keyword arguments respectively.

    Args:
        interface_name: The name of the interface. The interface must be stored in the ``ignis/dbus/`` directory in the Ignis sources.
        path: The full path to the interface XML.
        xml: The XML string.

    Raises:
        TypeError: If neither of the arguments is provided.

    Returns:
        The interface information.
    """
    xml_string: str

    if interface_name:
        file_path = f"{DBUS_DIR}/{interface_name}.xml"
        with open(file_path) as file:
            xml_string = file.read()
    elif path:
        with open(path) as file:
            xml_string = file.read()
    elif xml:
        xml_string = xml
    else:
        raise TypeError(
            "load_interface_xml() requires at least one positional argument"
        )

    return Gio.DBusNodeInfo.new_for_xml(xml_string).interfaces[0]

