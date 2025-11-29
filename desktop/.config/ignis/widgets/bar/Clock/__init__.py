from datetime import datetime
from typing import Any, Callable
from ignis.gobject import IgnisGObject
from ignis.utils import Utils
from ignis.widgets import Widget
import os
import util


SETTINGS_PATH = os.path.expanduser("~/.local/share/ignis/clock.json")

@util.JsonSettings(SETTINGS_PATH)
class ClockSettings(IgnisGObject):
    use_24h: bool = True
    def set_use_24h(self, value: bool) -> None: self.use_24h = value

    show_dow: bool = True
    def set_show_dow(self, value: bool) -> None: self.show_dow = value

    show_seconds: bool = True
    def set_show_seconds(self, value: bool) -> None: self.show_seconds = value

    @property
    def time_format(self) -> str:
        fmt = ""
        if self.show_dow:
            fmt += "%a "
        fmt += "%-d %b  "

        if self.use_24h:
            return fmt + ("%H:%M:%S" if self.show_seconds else "%H:%M")
        return fmt + ("%I:%M:%S %p" if self.show_seconds else "%I:%M %p")

clock_settings = ClockSettings()

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
                        label=clock_settings.bind_many(
                            ["use_24h", "show_dow", "show_seconds"],
                            lambda *_: Utils.Poll(1000, lambda _: datetime.now().strftime(clock_settings.time_format)).bind("output")
                        )
                    ),
                    css_classes=["box"],
                ),
            ],
            on_hover=on_hover,
            on_hover_lost=on_hover_lost,
        )

        util.popup_manager.register_popup_trigger("ignis_notifs_calendar", monitor, self)
