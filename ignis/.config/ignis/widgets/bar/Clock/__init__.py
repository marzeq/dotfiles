from datetime import datetime
from ignis.app import IgnisApp
from ignis.utils import Utils
from ignis.widgets import Widget
from ignis.options import options

app = IgnisApp.get_default()

def Clock(display_seconds: bool = True):
    root = Widget.Button(
        css_classes=["clock"],
        child=Widget.Box(
            child=[
                Widget.Box(
                    child=[
                        Widget.Label(
                            label=Utils.Poll(1_000, lambda _: datetime.now().strftime("%a %-d %b  %H:%M" + (":%S" if display_seconds else ""))).bind("output"))
                    ],
                    css_classes=["box"],
                ),
                Widget.Icon(
                    image="notifications-disabled-symbolic",
                    css_classes=["dnd-icon"],
                    visible=options.notifications.bind("dnd") # type: ignore
                ),
            ],
        ),
        on_click=lambda _: app.toggle_window("ignis_notifs_calendar") or app.close_window("ignis_control_centre")
    )

    def set_root_css_classes(*_):
        root.css_classes = ["clock", "clock-dnd"] if options.notifications.dnd else ["clock"] # type: ignore

    options.notifications.connect("changed", set_root_css_classes, "dnd") # type: ignore

    return root
