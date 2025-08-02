from ignis.utils import Utils
from ignis.app import IgnisApp
from widgets.bar.Bar import Bar
from widgets.bar.ControlCentre import ControlCentre
from widgets.bar.NotifsCalendar import NotifsCalendar
from widgets.misc.NotificationPopup import NotificationPopup
from widgets.misc.OSD import OSD

app = IgnisApp().get_default()
app.apply_css(f"{Utils.get_current_dir()}/style.scss") # type: ignore
app.add_icons(f"{Utils.get_current_dir()}/icons") # type: ignore

NotifsCalendar()
ControlCentre()

for i in range(Utils.get_n_monitors()): # type: ignore
    Bar(i)
    NotificationPopup(i)

OSD()
