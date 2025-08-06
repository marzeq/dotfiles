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

def run_cmd_and_run_delayed(cmd: str, runnable: Callable, delay: int) -> None:
    runnable()
    Utils.Timeout(delay, lambda *_: run_cmd(cmd))


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
