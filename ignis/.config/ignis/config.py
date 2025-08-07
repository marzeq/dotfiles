from ignis.utils import Utils
from ignis.app import IgnisApp
import utils
from widgets.bar.Bar import Bar
from widgets.bar.ClosePopupers import ClosePopuper
from widgets.bar.ControlCentre import ControlCentre
from widgets.bar.NotifsCalendar import NotifsCalendar
from widgets.misc.Launcher import LauncherProxy, Launcher
from widgets.misc.NotificationPopup import NotificationPopup
from widgets.misc.OSD import OSD
from widgets.misc.Settings import Settings

app = IgnisApp().get_default()
dir = Utils.get_current_dir() # type: ignore
app.apply_css(f"{dir}/style.scss")
app.add_icons(f"{dir}/icons")


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
