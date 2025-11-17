from ignis.utils import Utils
from ignis.widgets import Widget

import util
from widgets.bar.Clock import Clock
from widgets.bar.Workspaces import Workspaces 
from widgets.bar.Tray import Tray 

app = util.get_app()

class Bar(Widget.Window):
    def set_clock_hovered(self, value: bool):
        self.clock_hovered = value

    def set_tray_hovered(self, value: bool):
        self.tray_hovered = value

    def handle_click(self):
        if self.clock_hovered:
            util.popup_manager.handle_popup_clicked("ignis_notifs_calendar")
        elif self.tray_hovered:
            util.popup_manager.handle_popup_clicked("ignis_control_centre")
        else:
            util.popup_manager.close_curr_popup()

    def __init__(self, monitor_id: int = 0):
        monitor_name = Utils.get_monitor(monitor_id).get_connector()  # type: ignore

        self.clock_hovered = False
        self.tray_hovered = False

        super().__init__(
            namespace=f"ignis_bar_{monitor_id}",
            monitor=monitor_id,
            anchor=["left", "top", "right"],
            css_classes=["window"],
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
                                    monitor=monitor_id,
                                    on_hover=lambda *_: self.set_clock_hovered(True),
                                    on_hover_lost=lambda *_: self.set_clock_hovered(False),
                                ),
                            ],
                        ),
                        end_widget=Widget.Box(
                            child=[
                                Tray(
                                    monitor=monitor_id,
                                    on_hover=lambda *_: self.set_tray_hovered(True),
                                    on_hover_lost=lambda *_: self.set_tray_hovered(False),
                                ),
                            ],
                        ),
                        hexpand=True,
                    ),
                ],
                on_click=lambda *_: self.handle_click(),
            ),
        )
