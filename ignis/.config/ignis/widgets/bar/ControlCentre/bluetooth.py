import asyncio
from ignis.services.bluetooth import BluetoothDevice, BluetoothService
from widgets.bar.ControlCentre.popup_registry import popup_registry
from widgets.bar.ControlCentre.device_list_popup import DeviceListPopup
from widgets.bar.ControlCentre.widget import CCWLabels, ControlCentreWidget

bluetooth = BluetoothService.get_default()

def bt_connect(dev: BluetoothDevice) -> None:
    asyncio.create_task(dev.connect_to())

def bt_disconnect(dev: BluetoothDevice) -> None:
    asyncio.create_task(dev.disconnect_from())

class BluetoothPopup(DeviceListPopup):
    def __init__(self) -> None:
        super().__init__(
            title="Bluetooth",
            device=bluetooth,
            item_key="devices",
            icon_name_fn=lambda d: d.icon_name,
            label_fn=lambda d: d.alias or d.name,
            connect_fn=bt_connect,
            disconnect_fn=bt_disconnect,
            header_icon="bluetooth-symbolic",
            connected_property="connected",
            connected_check=lambda connected: connected
        )

    def filter_items(self, items: list[BluetoothDevice]) -> list[BluetoothDevice]:
        return sorted(items, key=lambda d: (not d.connected, d.alias or d.name))


class BluetoothWidget(ControlCentreWidget):
    def __init__(self):
        self.popup = BluetoothPopup()
        popup_registry.register(self.popup)
        super().__init__(
            icon=bluetooth.bind(
                "state",
                lambda state: "bluetooth-active-symbolic" if state == "on" and bluetooth.powered else "bluetooth-disabled-symbolic"
            ),
            labels=CCWLabels("Bluetooth"),
            on_click=lambda _: bluetooth.set_powered(False) if bluetooth.powered else bluetooth.set_powered(True),
            on_click_other=lambda _: popup_registry.close_all_but(self.popup) or self.popup.toggle(),
        )

        bluetooth.connect("notify::state", lambda *_: self.set_disabled(bluetooth.state == "absent" or not bluetooth.powered))
        bluetooth.connect("notify::powered", lambda *_: self.set_disabled(bluetooth.state == "absent" or not bluetooth.powered))
