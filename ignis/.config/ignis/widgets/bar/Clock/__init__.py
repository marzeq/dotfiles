from datetime import datetime
from typing import Any, Callable
from ignis.utils import Utils
from ignis.widgets import Widget
from ignis.options import options

import utils

def Clock(
    monitor: int,
    on_hover: Callable[..., Any],
    on_hover_lost: Callable[..., Any]
):
    box = Widget.EventBox(
        css_classes=["clock"],
        child=[
            Widget.Button(
                child=Widget.Label(
                    label=Utils.Poll(1_000, lambda _: datetime.now().strftime("%a %-d %b  %H:%M:%S")).bind("output")
                ),
                css_classes=["box"],
            ),
            Widget.Icon(
                image="notifications-disabled-symbolic",
                css_classes=["dnd-icon"],
                visible=options.notifications.bind("dnd") # type: ignore
            ),
        ],
        on_hover=on_hover,
        on_hover_lost=on_hover_lost,
    )

    def set_root_css_classes(*_):
        if options.notifications.dnd: # type: ignore
            box.css_classes = box.css_classes + ["clock-dnd"]
        else:
            box.css_classes = [clas for clas in box.css_classes if clas != "clock-dnd"]

    options.notifications.connect("changed", set_root_css_classes, "dnd") # type: ignore

    utils.popup_triggers_by_name[f"ignis_notifs_calendar_{monitor}"] = box

    return box
