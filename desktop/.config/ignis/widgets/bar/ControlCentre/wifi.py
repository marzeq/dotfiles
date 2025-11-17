import asyncio
from ignis.services.network import NetworkService, WifiAccessPoint, WifiDevice
from widgets.bar.ControlCentre.device_list_popup import DeviceListPopup
from widgets.bar.ControlCentre.popup_registry import popup_registry
from widgets.bar.ControlCentre.widget import CCWLabels, ControlCentreWidget

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


def wifi_connect(ap: WifiAccessPoint) -> None:
    asyncio.create_task(ap.connect_to_graphical())

def wifi_disconnect(ap: WifiAccessPoint) -> None:
    asyncio.create_task(ap.disconnect_from())

class WiFiPopup(DeviceListPopup[WifiAccessPoint]):
    def __init__(self) -> None:
        dev: WifiDevice | None = network.wifi.devices[0] if network.wifi.devices else None

        super().__init__(
            title="Wi-Fi",
            device=dev,
            item_key="access_points",
            icon_name_fn=lambda ap: ap.bind("icon_name"),
            label_fn=lambda ap: ap.bind("ssid"),
            connect_fn=wifi_connect,
            disconnect_fn=wifi_disconnect,
            header_icon="network-wireless-symbolic",
            connected_property="is_connected",
            connected_check=lambda is_connected: is_connected
        )

    def filter_items(self, items):
        return pick_strongest_aps_for_each_ssid(items)


class WiFiWidget(ControlCentreWidget):
    def __init__(self):
        self.popup = WiFiPopup()
        popup_registry.register(self.popup)

        super().__init__(
            icon=network.wifi.bind("icon_name"),
            labels=network.wifi.devices[0].bind_many(["is_connected", "ap"], lambda is_connected, ap: CCWLabels("Wi-Fi", ap.ssid) if is_connected and ap else CCWLabels("Wi-Fi")) if network.wifi.devices else CCWLabels("Wi-Fi"),
            on_click=lambda _: network.wifi.set_enabled(False) if network.wifi.enabled else network.wifi.set_enabled(True),
            on_click_other=lambda _: popup_registry.close_all_but(self.popup) or self.popup.toggle(),
        )

        self.set_disabled(not network.wifi.enabled)
        network.wifi.connect("notify::enabled", lambda *_: self.set_disabled(not network.wifi.enabled))
