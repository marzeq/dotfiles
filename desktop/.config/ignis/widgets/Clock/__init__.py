import asyncio
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
            return "%I:%M:%S" if show_seconds else "%I:%M"
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
        self.label = Widget.Label(label="")

        super().__init__(
            css_classes=["clock"],
            child=[
                Widget.Button(
                    child=self.label,
                    css_classes=["box"],
                ),
            ],
            on_hover=on_hover,
            on_hover_lost=on_hover_lost,
        )

        util.popup_manager.register_popup_trigger(
            "ignis_notifs_calendar", monitor, self
        )

        self._update_task: asyncio.Task[None] | None = None
        self.connect("realize", self._start_update)
        self.connect("unrealize", self._stop_update)

    def _start_update(self, *_args) -> None:
        if self._update_task is None or self._update_task.done():
            self._update_task = util.create_task(self.update_time())

    def _stop_update(self, *_args) -> None:
        if self._update_task is not None:
            self._update_task.cancel()
            self._update_task = None
    
    async def update_time(self):
        while True:
            self.label.set_label(
                datetime.now().strftime(
                    clock_settings.date_format(long=False, show_dow=clock_settings.show_dow)
                    + "  "
                    + clock_settings.hour_format(
                        show_seconds=clock_settings.show_seconds,
                        show_am_pm=True,
                    )
                )
            )
            await asyncio.sleep(1)
