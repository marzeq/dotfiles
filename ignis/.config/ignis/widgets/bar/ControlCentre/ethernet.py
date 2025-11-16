from ignis.services.network import NetworkService
import util
from widgets.bar.ControlCentre.widget import CCWLabels, ControlCentreWidget


network = NetworkService.get_default()

class EthernetWidget(ControlCentreWidget):
    def __init__(self):
        super().__init__(
            icon=network.ethernet.bind("icon_name"),
            labels=CCWLabels("Wired"),
            on_click=lambda _: util.run_cmd((
                "iface=$(nmcli -t -f DEVICE,TYPE,STATE device | awk -F':' '$2==\"ethernet\"{print $1; exit}'); "
                "state=$(nmcli -t -f DEVICE,STATE device | grep \"^$iface\" | cut -d':' -f2); "
                "[ $state = connected ] && "
                "nmcli device disconnect $iface || "
                "nmcli device connect $iface"
            )),
            on_click_other=lambda _: util.run_cmd_and_run("nm-connection-editor", lambda: util.popup_manager.close_curr_popup()),
        )

        self.set_disabled(not network.ethernet.is_connected)
        network.ethernet.connect("notify::is-connected", lambda *_: self.set_disabled(not network.ethernet.is_connected))
