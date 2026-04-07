from ignis.widgets import Widget
import util
from widgets.NotifsCalendar.calendar import Calendar
from widgets.NotifsCalendar.notifications import Notifications
from gi.repository import Gtk  # pyright: ignore[reportMissingModuleSource]

app = util.get_app()


class NotifsCalendar(Widget.RevealerWindow):
    def __init__(self, monitor: int):
        revealer = Widget.Revealer(
            transition_type="slide_down",
            child=Widget.Box(
                vertical=True,
                css_classes=["notifs-calendar-container"],
                child=[
                    Widget.Grid(
                        column_num=2,
                        css_classes=["notifs-calendar"],
                        child=[
                            Notifications(),
                            Calendar(),
                        ],
                    )
                ],
            ),
            transition_duration=util.popup_manager.popup_anim_speed,
            reveal_child=True,
        )

        super().__init__(
            visible=False,
            popup=True,
            kb_mode="on_demand",
            layer="top",
            anchor=["top", "right", "bottom", "left"],
            monitor=monitor,
            namespace=f"ignis_notifs_calendar_{monitor}",
            css_classes=["window"],
            child=Widget.Overlay(
                child=Widget.EventBox(
                    vexpand=True,
                    hexpand=True,
                    on_click=lambda _: util.popup_manager.close_curr_popup(),
                ),
                overlays=[
                    Widget.Box(
                        vertical=True,
                        valign="start",
                        halign="end" if util.has_apple_m2_notch() else "center",
                        child=[revealer],
                    ),
                ],
            ),
            revealer=revealer,
        )

        key_controller = Gtk.EventControllerKey()
        self.add_controller(key_controller)
        key_controller.connect(
            "key-pressed",
            lambda *x: util.popup_manager.clear_popupers()
            or util.popup_manager.reset_popup()
            if x[1] == 65307
            else None,
        )  # 65307 = ESC
