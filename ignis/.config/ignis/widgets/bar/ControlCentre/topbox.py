import math

from ignis.services.upower import UPowerService
from ignis.widgets import Widget

import util
from widgets.bar.ControlCentre.power_menu import PowerMenu

app = util.get_app()
upower = UPowerService.get_default()


class TopBox(Widget.CenterBox):
    def __init__(self, power_menu: PowerMenu):
        self.power_menu = power_menu
        super().__init__(
            css_classes=["control-centre-top"],
            start_widget=Widget.Box(child=upower.bind("batteries", self._start_children)),
            end_widget=Widget.Box(child=upower.bind("batteries", self._end_children))
        )

    def _start_children(self, _):
        settings_button = Widget.Button(
            child=Widget.Icon(image="applications-system-symbolic"),
            css_classes=["cc-top-button"],
            on_click=lambda _: app.open_window("ignis_settings") or util.popup_manager.close_curr_popup()
        )

        children = [
            Widget.Button(
                child=Widget.Icon(image="screenshooter-symbolic"),
                css_classes=["cc-top-button"],
                on_click=lambda _: util.run_cmd_and_run_delayed(
                    "hyprshot -szm region -o ~/pictures/screenshots/",
                    lambda: util.popup_manager.close_curr_popup(),
                    100
                ),
            )
        ]

        if len(upower.batteries) == 0:
            children += [settings_button]
        else:
            batt = upower.batteries[0]
            children += [
                Widget.Button(
                    child=Widget.Box(child=[
                        Widget.Icon(image=batt.icon_name),
                        Widget.Label(label=f"{math.floor(batt.percent)}%")
                    ]),
                    css_classes=["cc-top-button"],
                )
            ]
        return children

    def _end_children(self, _):
        settings_button = Widget.Button(
            child=Widget.Icon(image="applications-system-symbolic"),
            css_classes=["cc-top-button"],
            on_click=lambda _: app.open_window("ignis_settings") or util.popup_manager.close_curr_popup()
        )

        children = ([] if len(upower.batteries) == 0 else [settings_button]) + [
            Widget.Button(
                child=Widget.Icon(image="system-lock-screen-symbolic"),
                css_classes=["cc-top-button"],
                on_click=lambda _: util.run_cmd_and_run_delayed(
                    "loginctl lock-session",
                    lambda *_: util.popup_manager.close_curr_popup(),
                    100
                ),
            ),
            Widget.Button(
                child=Widget.Icon(image="system-shutdown-symbolic"),
                css_classes=["cc-top-button"],
                on_click=lambda *_: self.power_menu.toggle(),
            ),
        ]
        return children
