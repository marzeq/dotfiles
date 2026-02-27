import asyncio
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
        super().__init__(
            css_classes=["control-centre-top"],
            start_widget=Widget.Box(
                child=upower.bind("batteries", self._start_children)
            ),
            end_widget=Widget.Box(child=upower.bind("batteries", self._end_children)),
        )

    def _start_children(self, _):
        settings_button = Widget.Button(
            child=Widget.Icon(image="applications-system-symbolic"),
            css_classes=["cc-top-button"],
            on_click=lambda _: app.open_window("ignis_settings")
            or util.popup_manager.close_curr_popup(),
        )

        async def close_popup_before_screenshot():
            self.cc.revealer.transition_duration = 0
            util.popup_manager.close_curr_popup()
            self.cc.revealer.transition_duration = util.popup_manager.popup_anim_speed
            # await asyncio.sleep(util.popup_manager.popup_anim_speed / 1000)

        children = [
            Widget.Button(
                child=Widget.Icon(image="screenshooter-symbolic"),
                css_classes=["cc-top-button"],
                on_click=lambda _: util.shell(
                    "hyprshot -szm region -o ~/pictures/screenshots/",
                    before=close_popup_before_screenshot(),
                ),
            )
        ]

        if len(upower.batteries) == 0:
            children += [settings_button]
        else:
            batt = upower.display_device
            bat_percent = Widget.Button(
                child=Widget.Box(
                    child=[
                        Widget.Icon(
                            image=batt.bind("icon_name"),
                            # css_classes=batt.bind(
                            #     "charging",
                            #     lambda *_: ["battery-charging"] if batt.charging else [],
                            # ),
                        ),
                        Widget.Label(
                            label=batt.bind("percent", lambda *_: f"{math.floor(batt.percent)}%"),
                            css_classes=["cc-battery-percent"],
                        ),
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

            async def update_battery_tooltip_loop():
                while True:
                    await asyncio.sleep(update_battery_tooltip())
            task = asyncio.create_task(update_battery_tooltip_loop())

            def re_run_loop():
                nonlocal task
                task.cancel()
                task = asyncio.create_task(update_battery_tooltip_loop())

            batt.connect("notify::charging", lambda *_: re_run_loop())

            children += [bat_percent]
        return children

    def _end_children(self, _):
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
                on_click=lambda _: util.popup_manager.close_curr_popup() or lock(),
            ),
            Widget.Button(
                child=Widget.Icon(image="system-shutdown-symbolic"),
                css_classes=["cc-top-button"],
                on_click=lambda *_: popup_registry.close_all_but(self.power_menu)
                or self.power_menu.toggle(),
            ),
        ]
        return children
