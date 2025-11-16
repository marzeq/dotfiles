from ignis.services.bluetooth import BluetoothService
import util
from widgets.bar.ControlCentre.widget import CCWLabels, ControlCentreWidget

bluetooth = BluetoothService.get_default()

class BluetoothWidget(ControlCentreWidget):
    def __init__(self):
        super().__init__(
            icon=bluetooth.bind(
                "state",
                lambda state: "bluetooth-active-symbolic" if state == "on" and bluetooth.powered else "bluetooth-disabled-symbolic"
            ),
            labels=CCWLabels("Bluetooth"),
            on_click=lambda _: bluetooth.set_powered(False) if bluetooth.powered else bluetooth.set_powered(True),
            on_click_other=lambda _: util.run_cmd_and_run("blueberry", lambda: util.popup_manager.close_curr_popup()),
        )
        bluetooth.connect("notify::state", lambda *_: self.set_disabled(bluetooth.state == "absent" or not bluetooth.powered))
        bluetooth.connect("notify::powered", lambda *_: self.set_disabled(bluetooth.state == "absent" or not bluetooth.powered))
