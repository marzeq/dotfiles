import math

from ignis.services.upower import UPowerService
from ignis.widgets import Widget

import util
from widgets.Lockscreen import lock
from widgets.ControlCentre.popup_registry import popup_registry
from widgets.ControlCentre.power_menu import PowerMenu

app = util.get_app()
upower = UPowerService.get_default()


class TopBox(Widget.CenterBox):
    def __init__(self, power_menu: PowerMenu, cc: Widget.RevealerWindow):
        self.power_menu = power_menu
        self.cc = cc
        self._battery_handlers: list[tuple[object, int]] = []
        self._start = Widget.Box()
        self._end = Widget.Box()
        super().__init__(
            css_classes=["control-centre-top"],
            start_widget=self._start,
            end_widget=self._end,
        )
        upower.connect("notify::batteries", self._rebuild)
        self._rebuild()

    async def close_popup_immediately(self):
        self.cc.revealer.transition_duration = 0
        util.popup_manager.close_curr_popup()
        self.cc.revealer.transition_duration = util.popup_manager.popup_anim_speed
        # await asyncio.sleep(util.popup_manager.popup_anim_speed / 1000)

    def _disconnect_battery(self) -> None:
        for battery, handler in self._battery_handlers:
            if battery.handler_is_connected(handler):
                battery.disconnect(handler)
        self._battery_handlers.clear()

    def _rebuild(self, *_args) -> None:
        self._disconnect_battery()
        util.replace_box_children(self._start, self._start_children())
        util.replace_box_children(self._end, self._end_children())

    def _start_children(self):
        settings_button = Widget.Button(
            child=Widget.Icon(image="applications-system-symbolic"),
            css_classes=["cc-top-button"],
            on_click=lambda _: app.open_window("ignis_settings")
            or util.popup_manager.close_curr_popup(),
        )

        children = [
            Widget.Button(
                child=Widget.Icon(image="screenshooter-symbolic"),
                css_classes=["cc-top-button"],
                on_click=lambda _: util.shell(
                    "hyprshot -szm region -o ~/pictures/screenshots/",
                    before=self.close_popup_immediately,
                ),
            )
        ]

        if len(upower.batteries) == 0:
            children += [settings_button]
        else:
            batt = upower.display_device
            battery_icon = Widget.Icon(image=batt.icon_name)
            battery_label = Widget.Label(
                label=f"{math.floor(batt.percent)}%",
                css_classes=["cc-battery-percent"],
            )
            bat_percent = Widget.Button(
                child=Widget.Box(
                    child=[
                        battery_icon,
                        battery_label,
                    ]
                ),
                css_classes=["cc-top-button"],
            )

            def update_battery_tooltip() -> int:
                if batt.time_remaining <= 0:
                    bat_percent.set_tooltip_text("Calculating...")
                    return 3
                elif batt.charging:
                    bat_percent.set_tooltip_text(f"Full in {util.format_time(batt.time_remaining)}")
                else:
                    bat_percent.set_tooltip_text(f"{util.format_time(batt.time_remaining)} left")

                return 15

            def on_battery_update(*_):
                battery_icon.image = batt.icon_name
                battery_label.label = f"{math.floor(batt.percent)}%"
                update_battery_tooltip()

            for prop in ("icon-name", "percent", "charging", "time-remaining"):
                self._battery_handlers.append(
                    (batt, batt.connect(f"notify::{prop}", on_battery_update))
                )
            update_battery_tooltip()

            children += [bat_percent]
        return children

    def _end_children(self):
        settings_button = Widget.Button(
            child=Widget.Icon(image="applications-system-symbolic"),
            css_classes=["cc-top-button"],
            on_click=lambda _: app.open_window("ignis_settings")
            or util.popup_manager.close_curr_popup(),
        )

        children = ([] if len(upower.batteries) == 0 else [settings_button]) + [
            Widget.Button(
                child=Widget.Icon(image="system-lock-screen-symbolic"),
                css_classes=["cc-top-button"],
                on_click=lambda _: util.shell(
                    "loginctl lock-session",
                    before=self.close_popup_immediately,
                ),
            ),
            Widget.Button(
                child=Widget.Icon(image="system-shutdown-symbolic"),
                css_classes=["cc-top-button"],
                on_click=lambda *_: popup_registry.close_all_but(self.power_menu)
                or self.power_menu.toggle(),
            ),
        ]
        return children
