from typing import Any, Callable
from ignis.services.network import NetworkService
from ignis.services.audio import AudioService
from ignis.services.upower import UPowerService
from ignis.widgets import Widget
from ignis.options import options
import util

app = util.get_app()
network = NetworkService.get_default()
audio = AudioService.get_default()
upower = UPowerService.get_default()

class Tray(Widget.EventBox):
    def __init__(
        self,
        monitor: int,
        on_hover: Callable[..., Any],
        on_hover_lost: Callable[..., Any]
    ):
        self.network_icon = Widget.Icon(
            css_classes=["tray-icon"],
            image="network-wired-disconnected-symbolic"
        )

        network.ethernet.connect("notify::is-connected", lambda *_: self.update_network_icon())
        network.wifi.connect("notify::is-connected", lambda *_: self.update_network_icon())
        self.update_network_icon()

        self.power_icon = Widget.Icon(
            css_classes=["tray-icon"],
            image="system-shutdown-symbolic"
        )

        upower.connect("notify::batteries", lambda *_: self.update_power_icon())
        self.update_power_icon()

        super().__init__(
            css_classes=["tray"],
            child=[
                Widget.Button(
                    child=Widget.Box(
                        child=[
                            self.network_icon,
                            Widget.Icon(
                                css_classes=["tray-icon"],
                                image=audio.speaker.bind(  # type: ignore
                                    "icon_name",
                                    lambda icon: icon if icon != "image-missing" else "audio-volume-muted-symbolic"  # type: ignore
                                ),
                            ),
                            Widget.Icon(
                                css_classes=["tray-icon"],
                                image="notifications-disabled-symbolic",
                                visible=options.notifications.bind("dnd", lambda dnd: dnd)  # type: ignore
                            ),
                            self.power_icon,
                        ]
                    ),
                    css_classes=["box"]
                )
            ],
            on_hover=on_hover,
            on_hover_lost=on_hover_lost,
        )

        util.popup_manager.register_popup_trigger("ignis_control_centre", monitor, self)

    def update_network_icon(self):
        if network.ethernet.is_connected:
            self.network_icon.image = "network-wired-symbolic" # type: ignore
        elif network.wifi.is_connected:
            self.network_icon.image = "network-wireless-symbolic" # type: ignore
        else:
            self.network_icon.image = "network-wired-disconnected-symbolic" # type: ignore

    def update_power_icon(self):
        if len(upower.batteries) == 0:
            self.power_icon.image = "system-shutdown-symbolic"  # type: ignore
            return

        batt = upower.batteries[0]
        self.power_icon.image = batt.icon_name

