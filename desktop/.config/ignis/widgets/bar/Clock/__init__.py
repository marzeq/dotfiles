from datetime import datetime
from typing import Any, Callable
from ignis.utils import Utils
from ignis.widgets import Widget
import os
import util
import json


SETTINGS_PATH = os.path.expanduser("~/.local/share/ignis/clock.json")

class ClockSettings:
    def read_settings(self) -> None:
        try:
            with open(SETTINGS_PATH, "r") as f:
                settings = json.load(f)
        except FileNotFoundError:
            settings = {}
        
        self.use_24h = settings.get("use_24h", True)
        self.show_dow = settings.get("show_dow", True)
        self.show_seconds = settings.get("show_seconds", True)

    def save_settings(self) -> None:
        with open(SETTINGS_PATH, "w") as f:
            settings = {
                "use_24h": self.use_24h,
                "show_dow": self.show_dow,
                "show_seconds": self.show_seconds,
            }
            json.dump(settings, f, indent=2)

        self.time_format = self.get_time_format()

    def __init__(self):
        self.use_24h: bool
        self.show_dow: bool
        self.show_seconds: bool

        self.time_format: str

        self.read_settings()
        self.save_settings()

    def set_use_24h(self, use_24h: bool) -> None:
        self.use_24h = use_24h
        self.save_settings()

    def set_show_dow(self, show_dow: bool) -> None:
        self.show_dow = show_dow
        self.save_settings()

    def set_show_seconds(self, show_seconds: bool) -> None:
        self.show_seconds = show_seconds
        self.save_settings()

    def get_time_format(self) -> str:
        fmt = ""
        if self.show_dow:
            fmt += "%a "
        fmt += "%-d %b  "
        if self.use_24h:
            if self.show_seconds:
                fmt += "%H:%M:%S"
            else:
                fmt += "%H:%M"
        else:
            if self.show_seconds:
                fmt += "%I:%M:%S %p"
            else:
                fmt += "%I:%M %p"
        return fmt

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
                        label=Utils.Poll(100, lambda _: datetime.now().strftime(clock_settings.time_format)).bind("output")
                    ),
                    css_classes=["box"],
                ),
            ],
            on_hover=on_hover,
            on_hover_lost=on_hover_lost,
        )

        util.popup_manager.register_popup_trigger("ignis_notifs_calendar", monitor, self)
