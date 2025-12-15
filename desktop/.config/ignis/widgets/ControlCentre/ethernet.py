import asyncio
from ignis.services.network import Ethernet, EthernetDevice, NetworkService
import util
from widgets.ControlCentre.popup_registry import popup_registry
from widgets.ControlCentre.device_list_popup import DeviceListPopup
from widgets.ControlCentre.widget import CCWLabels, ControlCentreWidget

network = NetworkService.get_default()


def eth_connect(dev: EthernetDevice) -> None:
    asyncio.create_task(dev.connect_to())


def eth_disconnect(dev: EthernetDevice) -> None:
    asyncio.create_task(dev.disconnect_from())


class EthernetPopup(DeviceListPopup[EthernetDevice]):
    def __init__(self) -> None:
        eth: Ethernet | None = network.ethernet
        super().__init__(
            title="Wired Connections",
            device=eth,
            item_key="devices",
            icon_name_fn=lambda _: "network-wired-symbolic",
            label_fn=lambda d: d.bind_many(
                ["name", "perm_hw_address"], lambda name, addr: name or addr
            ),
            connect_fn=eth_connect,
            disconnect_fn=eth_disconnect,
            header_icon="network-wired-symbolic",
            connected_property="is_connected",
            connected_check=lambda is_connected: is_connected,
        )

    def filter_items(self, items):
        return sorted(
            items, key=lambda d: (not d.is_connected, d.name or d.perm_hw_address)
        )


class EthernetWidget(ControlCentreWidget):
    def __init__(self):
        self.popup = EthernetPopup()
        popup_registry.register(self.popup)

        super().__init__(
            icon=network.ethernet.bind("icon_name"),
            labels=CCWLabels("Wired"),
            on_click=lambda _: util.run_cmd(
                (
                    "iface=$(nmcli -t -f DEVICE,TYPE,STATE device | awk -F':' '$2==\"ethernet\"{print $1; exit}'); "
                    "state=$(nmcli -t -f DEVICE,STATE device | grep \"^$iface\" | cut -d':' -f2); "
                    "[ $state = connected ] && "
                    "nmcli device disconnect $iface || "
                    "nmcli device connect $iface"
                )
            ),
            on_click_other=lambda _: popup_registry.close_all_but(self.popup)
            or self.popup.toggle(),
        )

        self.set_disabled(network.ethernet.is_connected)
        network.ethernet.connect(
            "notify::is-connected",
            lambda *_: self.set_disabled(not network.ethernet.is_connected),
        )
