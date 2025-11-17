from datetime import datetime
from typing import Any, Callable
from ignis.utils import Utils
from ignis.widgets import Widget
import util

class Clock(Widget.EventBox):
    def __init__(
        self,
        monitor: int,
        on_hover: Callable[..., Any],
        on_hover_lost: Callable[..., Any]
    ):
        super().__init__(
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

        util.popup_manager.register_popup_trigger("ignis_notifs_calendar", monitor, self)
