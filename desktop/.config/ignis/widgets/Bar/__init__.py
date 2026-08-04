from ignis.services.hyprland import HyprlandService
from ignis.widgets import Widget
from ignis.utils.monitor import get_monitor

import util
from widgets.Clock import Clock
from widgets.Workspaces import Workspaces
from widgets.Tray import Tray
from widgets.Settings import hyprland_settings, bar_settings

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
        if not monitor_name:
            raise ValueError(f"Monitor with ID {monitor_id} has no connector name.")
        m2_notch = util.has_apple_m2_notch() and monitor_name == "eDP-1"

        self.clock_hovered = False
        self.tray_hovered = False

        clock = Clock(
            monitor=monitor_id,
            on_hover=lambda *_: self.set_clock_hovered(True),
            on_hover_lost=lambda *_: self.set_clock_hovered(
                False
            ),
        )

        cb = Widget.CenterBox(
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
                    cb,
                ],
                on_click=lambda *_: self.handle_click(),
            ),
        )


        matching = [m for m in util.hyprland.monitors if m.id == monitor_id]
        if len(matching) == 0:
            raise ValueError(f"Monitor with ID {monitor_id} does not exist.")
        hypr_monitor = matching[0]
        if bar_settings.show_only_on_primary_monitor and hypr_monitor.name != hyprland_settings.primary_monitor:
            self.visible = False

        def on_primary_show_changed(*_):
            if bar_settings.show_only_on_primary_monitor:
                return hypr_monitor.name == hyprland_settings.primary_monitor
            return True

        self.visible = bar_settings.bind("show_only_on_primary_monitor", on_primary_show_changed)

        def on_scale_changed(*_):
            style = ""
            if m2_notch:
                mh = 56 / hypr_monitor.scale
                style = f"min-height: {mh}px;"
            cb.style = style

        hypr_monitor.connect("notify::scale", on_scale_changed)
