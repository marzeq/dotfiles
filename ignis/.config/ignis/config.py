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
app.apply_css(f"{dir}/style.scss")
app.add_icons(f"{dir}/icons")

util.run_cmd("gsettings set org.gnome.desktop.interface gtk-theme adw-gtk3-dark")
util.run_cmd("gsettings set org.gnome.desktop.interface font-name 'Cantarell Regular 11'")
util.run_cmd("hyprctl reload")


for i in range(Utils.get_n_monitors()): # type: ignore
    ClosePopuper(i)
    Bar(i)
    NotificationPopup(i)
    NotifsCalendar(i)
    ControlCentre(i)
    Launcher(i)

OSD()
LauncherProxy()
Settings()
