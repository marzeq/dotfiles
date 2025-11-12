import os
from ignis.utils import Utils
import util
from widgets.bar.Bar import Bar
from widgets.bar.ClosePopupers import ClosePopuper
from widgets.bar.ControlCentre import ControlCentre
from widgets.bar.NotifsCalendar import NotifsCalendar
from widgets.misc.Launcher import LauncherProxy, Launcher
from widgets.misc.NotificationPopup import NotificationPopup
from widgets.misc.OSD import OSD
from widgets.misc.Settings import Settings

app = util.get_app()
dir = Utils.get_current_dir() # type: ignore

os.makedirs(os.path.expanduser("~/.local/share/ignis"), exist_ok=True)
accent_file = os.path.expanduser("~/.local/share/ignis/accent.scss")
if not os.path.exists(accent_file):
    with open(accent_file, "w") as f:
        f.write("")

app.apply_css(f"{dir}/style.scss")
app.add_icons(f"{dir}/icons")

util.run_cmd("gsettings set org.gnome.desktop.interface gtk-theme adw-gtk3-dark")
util.run_cmd("gsettings set org.gnome.desktop.interface font-name 'Cantarell Regular 11'")
util.run_cmd("hyprctl reload")


for i, m in enumerate(Utils.get_monitors()): # type: ignore
    ClosePopuper(i)
    Bar(i)
    NotificationPopup(i)
    NotifsCalendar(i)
    ControlCentre(i)
    Launcher(i, m)

OSD()
LauncherProxy()
Settings()
