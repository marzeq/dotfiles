import os
import util
import gc
import asyncio

from gi.repository import Gtk  # type: ignore[reportMissingModuleSource]

from ignis.utils import Utils

from widgets.Bar import Bar
from widgets.ClosePopupWidget import ClosePopupWidget
from widgets.ControlCentre import ControlCentre
from widgets.Lockscreen import LockProxy
from widgets.Calendar import Calendar
from widgets.Launcher import LauncherProxy, Launcher
from widgets.OSD import OSD
from widgets.Settings import SettingsWindow

app = util.get_app()

settings = Gtk.Settings.get_default()
if settings is not None:
    settings.set_property("gtk-application-prefer-dark-theme", True)

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
    ClosePopupWidget(i)
    Bar(i)
    Calendar(i)
    ControlCentre(i)
    Launcher(i, m)

OSD()
LauncherProxy()
SettingsWindow()
LockProxy()


async def cleanup_every(seconds: int):
    while True:
        gc.collect()
        await asyncio.sleep(seconds)

asyncio.create_task(cleanup_every(60))

def cleanup():
    util.sync_shell("gsettings reset org.gnome.desktop.wm.preferences button-layout")

app.connect("shutdown", lambda *_: cleanup())

