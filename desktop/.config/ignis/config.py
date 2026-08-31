import os
import util
import gc
import asyncio
import memory_profiler

from gi.repository import Gtk  # type: ignore[reportMissingModuleSource]

from ignis.utils import Utils

from widgets.Bar import Bar
from widgets.ClosePopupWidget import ClosePopupWidget
from widgets.ControlCentre import ControlCentre
from widgets.Lockscreen import LockProxy
from widgets.NotificationsAndCalendar import NotificationsAndCalendar
from widgets.NotificationsAndCalendar.notifications import NotificationPopups
from widgets.Launcher import LauncherProxy, Launcher
from widgets.OSD import OSD
from widgets.Settings import SettingsWindow

app = util.get_app()

# Opt in with IGNIS_MEMORY_PROFILE=1. Keep this near startup so the baseline
# includes allocations made while constructing all widgets below.
profiler_task = memory_profiler.start(os.path.dirname(os.path.abspath(__file__)))

settings = Gtk.Settings.get_default()
if settings is not None:
    settings.set_property("gtk-application-prefer-dark-theme", True)

dir = Utils.get_current_dir()  # type: ignore

os.makedirs(os.path.expanduser("~/.local/share/ignis"), exist_ok=True)
accent_file = os.path.expanduser("~/.local/share/ignis/accent.scss")
if not os.path.exists(accent_file):
    with open(accent_file, "w") as f:
        f.write("")
gtk_accent_file = os.path.expanduser("~/.local/share/ignis/gtk-accent.css")
if not os.path.exists(gtk_accent_file):
    accent_text_file = os.path.expanduser("~/.local/share/ignis/accent.txt")
    try:
        with open(accent_text_file) as f:
            accent_text = f.read().strip()
    except OSError:
        accent_text = ""
    accent_value = (
        f"#{accent_text}"
        if len(accent_text) == 6
        and all(character in "0123456789abcdefABCDEF" for character in accent_text)
        else "var(--accent-blue)"
    )
    with open(gtk_accent_file, "w") as f:
        f.write(f":root {{ --accent-bg-color: {accent_value}; }}\n")
theme_file = os.path.expanduser("~/.local/share/ignis/theme.scss")
if not os.path.exists(theme_file):
    with open(theme_file, "w") as f:
        f.write("")

app.apply_css(f"{dir}/style.scss")
app.apply_css(gtk_accent_file, style_priority="user")
app.add_icons(f"{dir}/icons")

util.shell("gsettings set org.gnome.desktop.interface gtk-theme adw-gtk3-dark")
util.shell("gsettings set org.gnome.desktop.interface font-name 'Adwaita Sans 11'")
util.shell("gsettings set org.gnome.desktop.wm.preferences button-layout :")
util.shell("hyprctl reload")


for i, m in enumerate(Utils.get_monitors()):  # type: ignore
    ClosePopupWidget(i)
    Bar(i)
    NotificationsAndCalendar(i)
    ControlCentre(i)
    Launcher(i, m)

NotificationPopups()
OSD()
LauncherProxy()
SettingsWindow()
LockProxy()


async def cleanup_every(seconds: int):
    while True:
        gc.collect()
        await asyncio.sleep(seconds)

util.create_task(cleanup_every(60))

def cleanup():
    util.cancel_background_tasks()
    util.sync_shell("gsettings reset org.gnome.desktop.wm.preferences button-layout")

app.connect("shutdown", lambda *_: cleanup())
