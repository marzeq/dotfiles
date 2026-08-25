from typing import Any, Callable
from ignis.services.network import NetworkService
from ignis.services.audio import AudioService
from ignis.services.upower import UPowerService
from ignis.widgets import Widget
from ignis.options import options
import util
from util import JsonSettings, BindableSettings

app = util.get_app()
network = NetworkService.get_default()
audio = AudioService.get_default()
upower = UPowerService.get_default()


@JsonSettings("tray")
class TraySettings(BindableSettings):
    show_batt_percent: bool = False

    def set_show_batt_percent(self, value: bool) -> None:
        self.show_batt_percent = value


tray_settings = TraySettings()



class Tray(Widget.EventBox):
    def __init__(
        self,
        monitor: int,
        on_hover: Callable[..., Any],
        on_hover_lost: Callable[..., Any],
    ):
        self._battery = None
        self._battery_handlers: list[int] = []
        self.network_icon = Widget.Icon(
            css_classes=["tray-icon"], image="network-wired-disconnected-symbolic"
        )

        def update_network(*_):
            self.update_network_icon()

        def update_power(*_):
            self.update_power_icon()

        network.ethernet.connect(
            "notify::is-connected", update_network
        )
        network.wifi.connect(
            "notify::is-connected", update_network
        )
        self.update_network_icon()

        self.power_icon = Widget.Icon(
            image="system-shutdown-symbolic"
        )
        self.batt_percent_label = Widget.Label(
            label=""
        )

        upower.connect("notify::batteries", update_power)
        tray_settings.connect("notify::show-batt-percent", self._refresh_battery)
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
                                    lambda icon: icon
                                    if icon != "image-missing"
                                    else "audio-volume-muted-symbolic",  # type: ignore
                                ),
                            ),
                            Widget.Icon(
                                css_classes=["tray-icon"],
                                image="notifications-disabled-symbolic",
                                visible=options.notifications.bind(   # type: ignore
                                    "dnd", lambda dnd: dnd
                                ),
                            ),
                            Widget.Box(
                                child=[
                                    self.power_icon,
                                    self.batt_percent_label,
                                ],
                                css_classes=["tray-icon"], 
                            ),
                        ]
                    ),
                    css_classes=["box"],
                )
            ],
            on_hover=on_hover,
            on_hover_lost=on_hover_lost,
        )

        util.popup_manager.register_popup_trigger("ignis_control_centre", monitor, self)

    def update_network_icon(self):
        if network.ethernet.is_connected:
            self.network_icon.image = "network-wired-symbolic"  # type: ignore
        elif network.wifi.is_connected:
            self.network_icon.image = "network-wireless-symbolic"  # type: ignore
        else:
            self.network_icon.image = "network-wired-disconnected-symbolic"  # type: ignore

    def update_power_icon(self):
        if self._battery is not None:
            for handler in self._battery_handlers:
                if self._battery.handler_is_connected(handler):
                    self._battery.disconnect(handler)
        self._battery_handlers.clear()
        self._battery = None

        if len(upower.batteries) == 0:
            self.power_icon.image = "system-shutdown-symbolic"  # type: ignore
            self.power_icon.css_classes = []
            self.batt_percent_label.label = ""
            self.batt_percent_label.css_classes = []
            return

        self._battery = upower.display_device
        for prop in ("icon-name", "charging", "percent"):
            self._battery_handlers.append(
                self._battery.connect(f"notify::{prop}", self._refresh_battery)
            )
        self._refresh_battery()

    def _refresh_battery(self, *_args):
        batt = self._battery
        if batt is None:
            return
        self.power_icon.image = batt.icon_name
        self.power_icon.css_classes = ["battery-charging"] if batt.charging else []
        show_percent = tray_settings.show_batt_percent
        self.batt_percent_label.label = f"{int(batt.percent)}%" if show_percent else ""
        self.batt_percent_label.css_classes = ["tray-batt-percent"] if show_percent else []
