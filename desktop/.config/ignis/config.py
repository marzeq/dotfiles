import os
from ignis.utils import Utils
import util
from widgets.Bar import Bar
from widgets.ClosePopupers import ClosePopuper
from widgets.ControlCentre import ControlCentre
from widgets.Lockscreen import LockProxy
from widgets.NotifsCalendar import NotifsCalendar
from widgets.Launcher import LauncherProxy, Launcher
from widgets.NotificationPopup import NotificationPopup
from widgets.OSD import OSD
from widgets.Settings import SettingsWindow

app = util.get_app()
dir = Utils.get_current_dir()  # type: ignore

os.makedirs(os.path.expanduser("~/.local/share/ignis"), exist_ok=True)
accent_file = os.path.expanduser("~/.local/share/ignis/accent.scss")
if not os.path.exists(accent_file):
    with open(accent_file, "w") as f:
        f.write("")
theme_file = os.path.expanduser("~/.local/share/ignis/theme.scss")
if not os.path.exists(theme_file):
    with open(theme_file, "w") as f:
        f.write("")

app.apply_css(f"{dir}/style.scss")
app.add_icons(f"{dir}/icons")

util.shell("gsettings set org.gnome.desktop.interface gtk-theme adw-gtk3-dark")
util.shell("gsettings set org.gnome.desktop.interface font-name 'Adwaita Sans 11'")
util.shell("gsettings set org.gnome.desktop.wm.preferences button-layout :")
util.shell("hyprctl reload")


for i, m in enumerate(Utils.get_monitors()):  # type: ignore
    ClosePopuper(i)
    Bar(i)
    NotificationPopup(i)
    NotifsCalendar(i)
    ControlCentre(i)
    Launcher(i, m)

OSD()
LauncherProxy()
SettingsWindow()
LockProxy()

import gc
import asyncio

async def cleanup_every(seconds: int):
    while True:
        gc.collect()
        await asyncio.sleep(seconds)

if getattr(app, "_ignis_cleanup_task", None) is None:
    app._ignis_cleanup_task = asyncio.create_task(cleanup_every(60))
