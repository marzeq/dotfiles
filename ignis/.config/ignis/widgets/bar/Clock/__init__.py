from datetime import datetime
from typing import Any, Callable
from ignis.utils import Utils
from ignis.widgets import Widget

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
        ],
        on_hover=on_hover,
        on_hover_lost=on_hover_lost,
    )

    utils.popup_triggers_by_name[f"ignis_notifs_calendar_{monitor}"] = box

    return box
