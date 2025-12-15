from datetime import datetime
from typing import Any, Callable
from ignis.utils import Utils
from ignis.widgets import Widget
import locale
from util import JsonSettings, BindableSettings
import util


def system_uses_24h():
    try:
        locale.setlocale(locale.LC_TIME, "")
        fmt = locale.nl_langinfo(locale.T_FMT)
        return "%p" not in fmt
    except Exception:
        return True


@JsonSettings("clock")
class ClockSettings(BindableSettings):
    use_24h: bool = system_uses_24h()

    def set_use_24h(self, value: bool) -> None:
        self.use_24h = value

    show_dow: bool = True

    def set_show_dow(self, value: bool) -> None:
        self.show_dow = value

    show_seconds: bool = True

    def set_show_seconds(self, value: bool) -> None:
        self.show_seconds = value

    def hour_format(self, show_seconds: bool, show_am_pm: bool) -> str:
        if self.use_24h:
            return "%H:%M:%S" if show_seconds else "%H:%M"
        if show_am_pm:
            return "%I:%M:%S %p" if show_seconds else "%I:%M %p"
        return "%I:%M:%S" if show_seconds else "%I:%M"

    def date_format(self, long: bool, show_dow: bool) -> str:
        if long:
            fmt = ""
            if show_dow:
                fmt += "%A "
            fmt += "%-d %B"
            return fmt

        fmt = ""
        if show_dow:
            fmt += "%a "
        fmt += "%-d %b"
        return fmt


clock_settings = ClockSettings()


class Clock(Widget.EventBox):
    def __init__(
        self,
        monitor: int,
        on_hover: Callable[..., Any],
        on_hover_lost: Callable[..., Any],
    ):
        super().__init__(
            css_classes=["clock"],
            child=[
                Widget.Button(
                    child=Widget.Label(
                        label=clock_settings.bind_properties(
                            lambda *_: Utils.Poll(
                                1000,
                                lambda _: datetime.now().strftime(
                                    clock_settings.date_format(
                                        long=False, show_dow=clock_settings.show_dow
                                    )
                                    + "  "
                                    + clock_settings.hour_format(
                                        show_seconds=clock_settings.show_seconds,
                                            show_am_pm=True
                                    )
                                ),
                            ).bind("output")
                        )
                    ),
                    css_classes=["box"],
                ),
            ],
            on_hover=on_hover,
            on_hover_lost=on_hover_lost,
        )

        util.popup_manager.register_popup_trigger(
            "ignis_notifs_calendar", monitor, self
        )
