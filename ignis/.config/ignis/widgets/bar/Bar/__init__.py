from ignis.utils import Utils
from ignis.widgets import Widget
from ignis.app import IgnisApp

import utils
from widgets.bar.Clock import Clock
from widgets.bar.Workspaces import Workspaces 
from widgets.bar.Tray import Tray 

app = IgnisApp.get_default()

def Bar(monitor_id: int = 0) -> Widget.Window:
    monitor_name = Utils.get_monitor(monitor_id).get_connector()  # type: ignore

    clock_hovered = False
    def set_clock_hovered(value: bool):
        nonlocal clock_hovered
        clock_hovered = value
    tray_hovered = False
    def set_tray_hovered(value: bool):
        nonlocal tray_hovered
        tray_hovered = value

    def handle_click():
        if clock_hovered:
            utils.handle_popup_clicked("ignis_notifs_calendar")
        elif tray_hovered:
            utils.handle_popup_clicked("ignis_control_centre")
        else:
            utils.close_curr_popup()
    
    return Widget.Window(
        namespace=f"ignis_bar_{monitor_id}",
        css_classes=["runset"],
        monitor=monitor_id,
        anchor=["left", "top", "right"],
        exclusivity="exclusive",
        child=Widget.EventBox(
            child=[
                Widget.CenterBox(
                    css_classes=["bar"],
                    start_widget=Widget.Box(
                        child=[
                            Workspaces(monitor_name),
                        ],
                    ),
                    center_widget=Widget.Box(
                        child=[
                            Clock(
                                on_hover=lambda *_: set_clock_hovered(True),
                                on_hover_lost=lambda *_: set_clock_hovered(False),
                            ),
                        ],
                    ),
                    end_widget=Widget.Box(
                        child=[
                            Tray(
                                on_hover=lambda *_: set_tray_hovered(True),
                                on_hover_lost=lambda *_: set_tray_hovered(False),
                            ),
                        ],
                    ),
                    hexpand=True,
                ),
            ],
            on_click=lambda *_: handle_click(),
        ),
    )
