import asyncio
from ignis.widgets import Widget
from datetime import datetime
import util


def get_month_days(month: int, year: int) -> int:
    if month == 2:
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):  # leap year check
            return 29
        else:
            return 28

    if month in [4, 6, 9, 11]:
        return 30

    return 31


def starting_dow_for_month(month: int, year: int) -> int:
    # zeller's congruence
    if month < 3:
        month += 12
        year -= 1
    q = 1
    K = year % 100
    J = year // 100
    h = (q + (13 * (month + 1)) // 5 + K + K // 4 + J // 4 + 5 * J) % 7

    # current setup: 0=saturday, 1=sunday, ..., 6=friday
    # adjust to monday=0, ..., sunday=6
    return (h + 5) % 7


def ending_dow_for_month(month: int, year: int) -> int:
    last_day = get_month_days(month, year)
    return (starting_dow_for_month(month, year) + last_day - 1) % 7


def calendar_month_reset_label(month: int, year: int) -> str:
    return (
        datetime(year, month, 1).strftime("%B")
        if year == datetime.now().year
        else datetime(year, month, 1).strftime("%B %Y")
    )


class CalendarGrid(Widget.Grid):
    def __init__(self, month: int, year: int):
        self._day_labels: list[Widget.Label] = [
            Widget.Label(
                label="",
                css_classes=["nc-calendar-day"],
                halign="center",
                valign="center",
            )
            for _ in range(42)
        ]

        headers = [
            Widget.Label(
                label=day,
                css_classes=["nc-calendar-dow-label"],
                halign="center",
                valign="center",
            )
            for day in ["M", "T", "W", "T", "F", "S", "S"]
        ]

        super().__init__(
            column_num=7,
            child=headers + self._day_labels,
        )

        self.set_month(month, year)

    def _set_day_label(self, widget: Widget.Label, day: int, extra_css: list[str]):
        widget.label = str(day).zfill(2)
        widget.css_classes = ["nc-calendar-day"] + extra_css

    def set_month(self, month: int, year: int):
        now = datetime.now()

        start_dow = starting_dow_for_month(month, year)
        month_days = get_month_days(month, year)

        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        prev_month_days = get_month_days(prev_month, prev_year)

        first_visible_day = prev_month_days - start_dow + 1

        day_specs: list[tuple[int, list[str]]] = [
            (day, ["nc-calendar-day-notcurrmo"])
            for day in range(first_visible_day, prev_month_days + 1)
        ]

        day_specs.extend(
            [
                (
                    day,
                    ["nc-calendar-day-currmo"]
                    + (
                        ["nc-calendar-day-today"]
                        if day == now.day
                        and month == now.month
                        and year == now.year
                        else []
                    )
                    + (
                        ["nc-calendar-day-workday"]
                        if (start_dow + day - 1) % 7 not in (5, 6)
                        else []
                    ),
                )
                for day in range(1, month_days + 1)
            ]
        )

        day_specs.extend(
            [
                (day, ["nc-calendar-day-notcurrmo"])
                for day in range(
                    1,
                    max(0, 42 - (start_dow + month_days)) + 1,
                )
            ]
        )

        for widget, (day, extra_css) in zip(self._day_labels, day_specs):
            self._set_day_label(widget, day, extra_css)


class Calendar(Widget.Box):
    def __init__(self):
        self.curr_month = True
        self.selected_month = datetime.now().month
        self.selected_year = datetime.now().year

        self.calendar_dow_label = Widget.Label(
            label=datetime.now().strftime("%A"),
            css_classes=["nc-calendar-dow"],
            halign="start",
        )

        self.calendar_date_label = Widget.Label(
            label=datetime.now().strftime("%d %B %Y"),
            css_classes=["nc-calendar-date"],
            halign="start",
        )

        self.calendar_month_reset_button = Widget.Button(
            child=Widget.Label(
                label=calendar_month_reset_label(
                    self.selected_month, self.selected_year
                ),
            ),
            css_classes=["nc-calendar-month"],
            on_click=self.reset_month,
        )

        self.calendar_grid_box = Widget.Box(
            child=[CalendarGrid(self.selected_month, self.selected_year)],
        )

        super().__init__(
            vertical=True,
            css_classes=["nc-calendar"],
            child=[
                self.calendar_dow_label,
                self.calendar_date_label,
                Widget.CenterBox(
                    start_widget=Widget.Button(
                        child=Widget.Icon(
                            image="pan-start-symbolic",
                        ),
                        css_classes=["nc-calendar-arrow"],
                        on_click=self.decrement_month,
                    ),
                    center_widget=self.calendar_month_reset_button,
                    end_widget=Widget.Button(
                        child=Widget.Icon(
                            image="pan-end-symbolic",
                        ),
                        css_classes=["nc-calendar-arrow"],
                        on_click=self.increment_month,
                    ),
                    css_classes=["nc-calendar-month-switcher"],
                ),
                self.calendar_grid_box,
            ],
        )

        self._update_task: asyncio.Task[None] | None = None
        self.connect("realize", self._start_update)
        self.connect("unrealize", self._stop_update)

    def _start_update(self, *_args) -> None:
        if self._update_task is None or self._update_task.done():
            self._update_task = util.create_task(self.async_update_loop())

    def _stop_update(self, *_args) -> None:
        if self._update_task is not None:
            self._update_task.cancel()
            self._update_task = None

    async def async_update_loop(self, *_):
        while True:
            self.update_calendar()
            await asyncio.sleep(15)


    def set_month(self, month: int, year: int):
        self.calendar_month_reset_button.child.label = calendar_month_reset_label(
            month, year
        )
        grid = self.calendar_grid_box.child[0]
        if isinstance(grid, CalendarGrid):
            grid.set_month(month, year)

    def reset_month(self, *_):
        self.selected_month = datetime.now().month
        self.selected_year = datetime.now().year
        self.curr_month = True

        self.set_month(self.selected_month, self.selected_year)

    def increment_month(self, *_):
        self.curr_month = False
        if self.selected_month == 12:
            self.selected_month = 1
            self.selected_year += 1
        else:
            self.selected_month += 1
        self.set_month(self.selected_month, self.selected_year)

    def decrement_month(self, *_):
        self.curr_month = False
        if self.selected_month == 1:
            self.selected_month = 12
            self.selected_year -= 1
        else:
            self.selected_month -= 1
        self.set_month(self.selected_month, self.selected_year)

    def update_calendar(self):
        self.calendar_dow_label.label = datetime.now().strftime("%A")
        self.calendar_date_label.label = datetime.now().strftime("%d %B %Y")
        if self.curr_month:
            self.selected_month = datetime.now().month
            self.selected_year = datetime.now().year
            self.set_month(self.selected_month, self.selected_year)
