from datetime import datetime
from ignis.widgets import Widget
from ignis.utils import Utils
from ignis.services.notifications import NotificationService
import util
from widgets.shared.Notification import NotificationWidget
from gi.repository import Gtk  # type: ignore

app = util.get_app()
notifications = NotificationService.get_default()

def get_month_days(month: int, year: int) -> int:
    if month == 2:
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0): # leap year check
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


def Notifications():
    notifs = notifications.notifications
                
    return Widget.Box(
        css_classes=["nc-notifications"],
        child=[
            Widget.Overlay(
                child=Widget.Box(
                    child=[
                        Widget.Button(
                            label="Clear",
                            on_click=lambda _: notifications.clear_all(),
                            css_classes=["nc-notifications-clear"],
                        )
                    ] if notifs else [],
                    css_classes=["nc-notifications-bottom"],
                    valign="end",
                ),
                overlays=[
                    Widget.Box(
                        vertical=True,
                        valign="center",
                        child=[
                            Widget.Icon(
                                image="no-notifications-symbolic",
                                css_classes=["nc-notifications-empty-icon"],
                                pixel_size=96,
                            ),
                            Widget.Label(
                                label="No notifications",
                                css_classes=["nc-notifications-empty-label"],
                            ),
                        ],
                    )
                ] if not notifs else [Widget.Scroll(
                    child=Widget.Box(
                        vertical=True,
                        child=[NotificationWidget(n, show_time=True) for n in notifs],
                    ),
                    css_classes=["nc-notifications-scroll"],
                )],
                hexpand=True,
            ),
        ],
    )

def CalendarGrid(month: int, year: int) -> Widget.Grid:
    return Widget.Grid(
        column_num=7,
        child=([
            Widget.Label(
                label=day,
                css_classes=["nc-calendar-dow-label"],
                halign="center",
            ) for day in ["M", "T", "W", "T", "F", "S", "S"]
        ] + [
                # previous month days to fill out the first week
                Widget.Label(
                    label=str(get_month_days(month - 1, year) - x).zfill(2),
                    css_classes=["nc-calendar-day", "nc-calendar-day-notcurrmo"],
                    halign="center",
                ) for x in range(
                    starting_dow_for_month(month, year)
                )
            ] + [
                # current month days
                Widget.Label(
                    label=str(day).zfill(2),
                    css_classes=
                    ["nc-calendar-day", "nc-calendar-day-currmo"] +
                        (["nc-calendar-day-today"] if day == datetime.now().day and datetime.now().month == month and datetime.now().year == year else []) +
                        (["nc-calendar-day-workday"] if (day+starting_dow_for_month(month, year) - 1) % 7 not in [5, 6] else []),
                    halign="center",
                ) for day in range(1, get_month_days(month, year) + 1)
            ] + [
                # next month days to fill out the last week
                Widget.Label(
                    label=str(day).zfill(2),
                    css_classes=["nc-calendar-day", "nc-calendar-day-notcurrmo"],
                    halign="center",
                ) for day in range(1, 43 - (starting_dow_for_month(month, year) + get_month_days(month, year)))
            ])
    )

def NotifsCalendar(monitor: int):
    curr_month = True
    selected_month = datetime.now().month
    selected_year = datetime.now().year

    calendar_dow = Widget.Label(
        label=datetime.now().strftime("%A"),
        css_classes=["nc-calendar-dow"],
        halign="start",
    )

    calendar_date = Widget.Label(
        label=datetime.now().strftime("%d %B %Y"),
        css_classes=["nc-calendar-date"],
        halign="start",
    )

    def calendar_month_reset_label(month: int, year: int) -> str:
        return datetime(year, month, 1).strftime("%B") if year == datetime.now().year else datetime(year, month, 1).strftime("%B %Y")

    calendar_month_reset = Widget.Button(
        child=Widget.Label(
            label=calendar_month_reset_label(selected_month, selected_year),
        ),
        css_classes=["nc-calendar-month"],
    )

    calendar_grid_box = Widget.Box(
        child=[CalendarGrid(selected_month, selected_year)],
    )

    def set_month(month: int, year: int):
        calendar_month_reset.child.label = calendar_month_reset_label(month, year)
        calendar_grid_box.child = [CalendarGrid(month, year)] # type: ignore

    def reset_month(*_):
        nonlocal selected_month, selected_year, curr_month
        selected_month = datetime.now().month
        selected_year = datetime.now().year
        curr_month = True
        set_month(selected_month, selected_year)

    calendar_month_reset.on_click = reset_month # type: ignore

    def increment_month(*_):
        nonlocal selected_month, selected_year, curr_month
        curr_month = False
        if selected_month == 12:
            selected_month = 1
            selected_year += 1
        else:
            selected_month += 1
        set_month(selected_month, selected_year)

    def decrement_month(*_):
        nonlocal selected_month, selected_year, curr_month
        curr_month = False
        if selected_month == 1:
            selected_month = 12
            selected_year -= 1
        else:
            selected_month -= 1
        set_month(selected_month, selected_year)

    calendar = Widget.Box(
        vertical=True,
        css_classes=["nc-calendar"],
        child=[
            calendar_dow,
            calendar_date,
            Widget.CenterBox(
                start_widget=Widget.Button(
                    child=Widget.Icon(
                        image="pan-start-symbolic",
                    ),
                    css_classes=["nc-calendar-arrow"],
                    on_click=decrement_month,
                ),
                center_widget=calendar_month_reset,
                end_widget=Widget.Button(
                    child=Widget.Icon(
                        image="pan-end-symbolic",
                    ),
                    css_classes=["nc-calendar-arrow"],
                    on_click=increment_month,
                ),
                css_classes=["nc-calendar-month-switcher"],
            ),
            calendar_grid_box,
        ],
    )

    box = Widget.Grid(
        column_num=2,
        css_classes=["notifs-calendar"],
        child=[
            Widget.Box(),
            calendar,
        ],
    )

    def update_calendar():
        nonlocal selected_month, selected_year, curr_month
        calendar_dow.label = datetime.now().strftime("%A")
        calendar_date.label = datetime.now().strftime("%d %B %Y")
        if curr_month:
            selected_month = datetime.now().month
            selected_year = datetime.now().year
            set_month(selected_month, selected_year)

    def update_notifications():
        box.child = [
            Notifications(),
            box.child[1],  # type: ignore
        ]

    update_notifications()

    notifications.connect("notify::notifications", lambda *_: update_notifications())
    Utils.Poll(60_000, lambda *_: update_notifications()) # to update the "X minutes ago" etc. labels

    Utils.Poll(60_000, lambda *_: update_calendar()) # to update the calendar if the month changes

    revealer = Widget.Revealer(
        transition_type="slide_down",
        child=Widget.Box(
            vertical=True,
            css_classes=["notifs-calendar-container"],
            child=[box],
        ),
        transition_duration=util.popup_manager.popup_anim_speed,
        reveal_child=True,
    )

    window = Widget.RevealerWindow(
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
                    halign="center",
                    child=[revealer],
                ),
            ],
        ),
        revealer=revealer,
    )

    key_controller = Gtk.EventControllerKey()
    window.add_controller(key_controller)
    key_controller.connect("key-pressed", lambda *x: util.popup_manager.clear_popupers() or util.popup_manager.reset_popup() if x[1] == 65307 else None)  # 65307 = ESC

    return window

