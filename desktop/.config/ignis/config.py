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
from widgets.KeyboardLayout import (
    KeyboardLayoutOSD,
    KeyboardLayoutPopup,
    KeyboardLayoutProxy,
)
from widgets.Settings import SettingsWindow, hyprland_settings

app = util.get_app()

# Opt in with IGNIS_MEMORY_PROFILE=1. Keep this near startup so the baseline
# includes allocations made while constructing all widgets below.
profiler_task = memory_profiler.start(os.path.dirname(os.path.abspath(__file__)))

settings = Gtk.Settings.get_default()
if settings is not None:
    settings.set_property("gtk-application-prefer-dark-theme", True)

dir = Utils.get_current_dir()  # type: ignore

os.makedirs(os.path.expanduser("~/.local/share/ignis"), exist_ok=True)
legacy_monitors_file = os.path.expanduser("~/.config/hypr/monitors.lua")
monitors_file = os.path.expanduser("~/.local/share/ignis/monitors.lua")
if os.path.exists(legacy_monitors_file) and not os.path.exists(monitors_file):
    os.replace(legacy_monitors_file, monitors_file)
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

# Flatpak's exported applications and icons may be absent from XDG_DATA_DIRS
# in the environment that starts Ignis.  The launcher discovers the desktop
# files explicitly; add the matching icon roots to GTK's theme as well.
data_home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
for flatpak_icon_dir in (
    os.path.join(data_home, "flatpak/exports/share/icons"),
    "/var/lib/flatpak/exports/share/icons",
):
    if os.path.isdir(flatpak_icon_dir):
        app.add_icons(flatpak_icon_dir)

util.shell("gsettings set org.gnome.desktop.interface gtk-theme adw-gtk3-dark")
util.shell("gsettings set org.gnome.desktop.interface font-name 'Adwaita Sans 11'")
util.shell("gsettings set org.gnome.desktop.wm.preferences button-layout :")
util.shell("hyprctl reload")


monitors = list(Utils.get_monitors())  # type: ignore
if not monitors:
    raise RuntimeError("Ignis could not find a display for the shell")
primary_monitor_id = util.monitor_id_for_connector(
    hyprland_settings.primary_monitor
)

for i, m in enumerate(monitors):
    ClosePopupWidget(i)
    Launcher(i, m)

Bar(primary_monitor_id)
KeyboardLayoutPopup(primary_monitor_id)
NotificationsAndCalendar(primary_monitor_id)
ControlCentre(primary_monitor_id)

NotificationPopups()
OSD(primary_monitor_id)
KeyboardLayoutOSD(primary_monitor_id)
KeyboardLayoutProxy()
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
