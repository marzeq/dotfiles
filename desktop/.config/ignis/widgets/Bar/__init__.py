from ignis.widgets import Widget
from ignis.utils.monitor import get_monitor

import util
from widgets.Clock import Clock
from widgets.Workspaces import Workspaces
from widgets.Tray import Tray

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
        monitor = get_monitor(monitor_id)
        if not monitor:
            raise ValueError(f"Monitor with ID {monitor_id} does not exist.")
        monitor_name = monitor.get_connector()
        m2_notch = util.has_apple_m2_notch() and monitor_name == "eDP-1"

        style = ""
        if m2_notch:
            sf = util.get_monitor_scale_factor(monitor_name)
            mh = 56 / sf
            style = f"min-height: {mh}px;"


        self.clock_hovered = False
        self.tray_hovered = False

        clock = Clock(
            monitor=monitor_id,
            on_hover=lambda *_: self.set_clock_hovered(True),
            on_hover_lost=lambda *_: self.set_clock_hovered(
                False
            ),
        )

        super().__init__(
            namespace=f"ignis_bar_{monitor_id}",
            monitor=monitor_id,
            anchor=["left", "top", "right"],
            css_classes=["window"],
            exclusivity="exclusive",
            layer="bottom",
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
                            child=[] if m2_notch else [clock],
                        ),
                        end_widget=Widget.Box(
                            child=([clock] if m2_notch else []) +
                            [
                                Tray(
                                    monitor=monitor_id,
                                    on_hover=lambda *_: self.set_tray_hovered(True),
                                    on_hover_lost=lambda *_: self.set_tray_hovered(
                                        False
                                    ),
                                ),
                            ],
                        ),
                        hexpand=True,
                        style=style,
                    ),
                ],
                on_click=lambda *_: self.handle_click(),
            ),
        )
