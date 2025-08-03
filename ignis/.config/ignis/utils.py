import subprocess
import os
from typing import Callable

from ignis.app import IgnisApp
from ignis.services.hyprland.service import HyprlandService
from ignis.utils import Utils

app = IgnisApp.get_default()
hyprland = HyprlandService.get_default()

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


# Popup management

popup_anim_speed = 100

curr_popup = None
curr_popup_monitor = None

def set_popup(name: str) -> None:
    global curr_popup, curr_popup_monitor
    curr_popup = name
    curr_popup_monitor = active_monitor()

def reset_popup() -> None:
    global curr_popup, curr_popup_monitor
    curr_popup = None
    curr_popup_monitor = None

def handle_popup_clicked(name: str) -> None:
    global curr_popup, curr_popup_monitor

    clear_popupers()
    if curr_popup == name:
        if curr_popup_monitor is None:
            app.open_window(name)
            set_popup(name)
        elif curr_popup_monitor == active_monitor():
            app.close_window(name)
            reset_popup()
        else:
            app.close_window(curr_popup) if curr_popup else None
            Utils.Timeout(ms=popup_anim_speed, target=lambda: app.open_window(name))
            set_popup(name)
    else:
        app.close_window(curr_popup) if curr_popup else None
        app.open_window(name)
        set_popup(name)

    open_popupers()

def close_any_popup() -> None:
    global curr_popup, curr_popup_monitor
    if curr_popup is not None:
        app.close_window(curr_popup)
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
