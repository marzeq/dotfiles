import asyncio
from ignis.services.network import NetworkService, WifiAccessPoint
from ignis.widgets import Widget
import util
from widgets.bar.ControlCentre.widget import CCWLabels, ControlCentrePopup, ControlCentreWidget

network = NetworkService.get_default()

def group_aps_by_ssid(aps: list[WifiAccessPoint]) -> dict[str, list[WifiAccessPoint]]:
    retdict: dict[str, list[WifiAccessPoint]] = {}
    for ap in aps:
        if not ap.ssid:
            continue
        retdict.setdefault(ap.ssid, []).append(ap)
    return retdict

def pick_strongest_aps_for_each_ssid(aps: list[WifiAccessPoint]) -> list[WifiAccessPoint]:
    grouped = group_aps_by_ssid(aps)
    strongest = [max(aps, key=lambda ap: ap.strength) for aps in grouped.values()]
    return sorted(strongest, key=lambda ap: ap.strength, reverse=True)


class WiFiPopup(ControlCentrePopup):
    def __init__(self):
        self.dev = network.wifi.devices[0] if network.wifi.devices else None
        if self.dev is None:
            super().__init__(Widget.Box())
            return

        self.wants_see_more = False 

        self.aps_box = Widget.Box(
            vertical=True,
            child=self.dev.bind("access_points", transform=self.render_networks)
        )

        super().__init__(
            Widget.Box(
                vertical=True,
                child=[
                    Widget.Box(
                        child=[
                            Widget.Icon(
                                image="network-wireless-symbolic",
                                css_classes=["cc-popup-icon"],
                                pixel_size=24,
                            ),
                            Widget.Label(
                                label="Wi-Fi Networks",
                                css_classes=["cc-popup-label"]
                            ),
                        ],
                        css_classes=["cc-popup-header"],
                        halign="start",
                    ),
                    self.aps_box
                ]
            )
        )

    def render_networks(self, aps: list[WifiAccessPoint]):
        filtered = pick_strongest_aps_for_each_ssid(aps)
        if not self.wants_see_more:
            filtered = filtered[:5]

        widgets = [
            Widget.Button(
                child=Widget.Box(
                    child=[
                        Widget.Icon(
                            image=ap.bind("strength", transform=lambda _: ap.icon_name),
                            pixel_size=18,
                            css_classes=["cc-popup-opt-icon"]
                        ),
                        Widget.Label(label=ap.ssid),
                    ],
                    css_classes=["cc-popup-opt-label"]
                ),
                on_click=lambda _, ap=ap: util.popup_manager.close_curr_popup() or asyncio.create_task(ap.connect_to_graphical()),
                css_classes=["cc-popup-option"],
            )
            for ap in filtered
        ]

        if len(filtered) < len(aps):
            widgets.append(
                Widget.Button(
                    label="See more networks" if not self.wants_see_more else "See fewer networks",
                    on_click=lambda _: self.toggle_see_more(),
                    css_classes=["cc-popup-option"],
                )
            )

        return widgets or [
            Widget.Label(label="No Wi-Fi networks found", css_classes=["cc-popup-no-wifi"])
        ]

    def toggle_see_more(self):
        self.wants_see_more = not self.wants_see_more
        
        self.aps_box.set_child(
            self.render_networks(self.dev.access_points) # type: ignore
        )

class WiFiWidget(ControlCentreWidget):
    def __init__(self):
        self.popup = WiFiPopup()

        super().__init__(
            icon=network.wifi.bind("icon_name"),
            labels=network.wifi.devices[0].bind_many(["is_connected", "ap"], lambda is_connected, ap: CCWLabels("Wi-Fi", ap.ssid) if is_connected and ap else CCWLabels("Wi-Fi")) if network.wifi.devices else CCWLabels("Wi-Fi"),
            on_click=lambda _: network.wifi.set_enabled(False) if network.wifi.enabled else network.wifi.set_enabled(True),
            on_click_other=lambda _: self.popup.toggle(),
        )

        self.set_disabled(not network.wifi.enabled)
        network.wifi.connect("notify::enabled", lambda *_: self.set_disabled(not network.wifi.enabled))
