from ignis.utils import Utils
from ignis.widgets import Widget

from widgets.bar.Clock import Clock
from widgets.bar.Workspaces import Workspaces 
from widgets.bar.Tray import Tray 

def Bar(monitor_id: int = 0) -> Widget.Window:
    monitor_name = Utils.get_monitor(monitor_id).get_connector()  # type: ignore
    
    return Widget.Window(
        namespace=f"ignis_bar_{monitor_id}",
        monitor=monitor_id,
        anchor=["left", "top", "right"],
        exclusivity="exclusive",
        child=Widget.CenterBox(
            css_classes=["bar"],
            start_widget=Widget.Box(
                child=[
                    Workspaces(monitor_name),
                ],
            ),
            center_widget=Widget.Box(
                child=[
                    Clock(),
                ],
            ),
            end_widget=Widget.Box(
                child=[
                    Tray(),
                ],
            ),
        ),
    )
