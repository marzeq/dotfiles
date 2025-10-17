import math
from typing import Callable

from ignis.services.upower import UPowerService
from ignis.widgets import Widget

import util


app = util.get_app()
upower = UPowerService.get_default()

def TopBox(power_menu_toggle: Callable):
    settings_button = Widget.Button(child=Widget.Icon(
        image="applications-system-symbolic"),
        css_classes=["cc-top-button"],
        on_click=lambda _: app.open_window("ignis_settings") or util.close_curr_popup(),
    )

    return Widget.CenterBox(
        css_classes=["control-centre-top"],
        start_widget=Widget.Box(child=upower.bind("batteries", lambda *_:
            [
                Widget.Button(child=Widget.Icon(
                    image=f"screenshooter-symbolic"), # type: ignore 
                    css_classes=["cc-top-button"],
                    on_click=lambda _: util.run_cmd_and_run_delayed("hyprshot -szm region -o ~/pictures/screenshots/", lambda: util.close_curr_popup(), 100),
                )
            ] + ([
                settings_button,
            ] if len(upower.batteries) == 0 else [
                Widget.Button(
                    child=Widget.Box(child=[
                        Widget.Icon(
                            image=upower.batteries[0].icon_name
                        ),
                        Widget.Label(
                            label=f"{math.floor(upower.batteries[0].percent)}%"
                        )
                    ]),
                    css_classes=["cc-top-button"],
                )
            ])
        )),
        end_widget=Widget.Box(
            child=([] if len(upower.batteries) == 0 else [settings_button]) + [
                Widget.Button(child=Widget.Icon(
                    image="system-lock-screen-symbolic"),
                    css_classes=["cc-top-button"],
                    on_click=lambda _: util.run_cmd_and_run_delayed("loginctl lock-session", lambda: util.close_curr_popup(), 100),
                ),
                Widget.Button(child=Widget.Icon(
                    image="system-shutdown-symbolic"),
                    css_classes=["cc-top-button"],
                    on_click=lambda _: power_menu_toggle()
                ),
            ]
        )
    )
