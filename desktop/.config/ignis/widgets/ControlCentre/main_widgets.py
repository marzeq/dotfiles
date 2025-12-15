from ignis.services.bluetooth import BluetoothService
from ignis.services.network import NetworkService
from ignis.widgets import Widget

from widgets.ControlCentre.bluetooth import BluetoothWidget
from widgets.ControlCentre.dnd import DNDWidget
from widgets.ControlCentre.ethernet import EthernetWidget
from widgets.ControlCentre.power_profiles import PowerProfilesWidget
from widgets.ControlCentre.wifi import WiFiWidget


network = NetworkService.get_default()
bluetooth = BluetoothService.get_default()


class MainWidgets(Widget.Box):
    def __init__(self):
        super().__init__(
            css_classes=["control-centre-widgets"],
            vertical=True,
            child=[],
        )

        self.ethernet_widget = EthernetWidget()
        network.ethernet.connect("notify::devices", lambda *_: self.update_widgets())

        self.wifi_widget = WiFiWidget()
        network.wifi.connect("notify::devices", lambda *_: self.update_widgets())

        self.bluetooth_widget = BluetoothWidget()
        bluetooth.connect("notify::state", lambda *_: self.update_widgets())

        self.power_profiles_widget = PowerProfilesWidget()

        self.dnd_widget = DNDWidget()

        self.rows: list[Widget.Box] = []

        self.update_widgets()

    def update_widgets(self):
        self.set_child([])
        self.rows.clear()

        widgets = []
        if network.ethernet.devices:
            widgets.append(self.ethernet_widget)
        if network.wifi.devices:
            widgets.append(self.wifi_widget)
        if bluetooth.state != "absent":
            widgets.append(self.bluetooth_widget)
        if self.power_profiles_widget.is_available():
            widgets.append(self.power_profiles_widget)
        widgets.append(self.dnd_widget)

        for i in range(0, len(widgets), 2):
            row = Widget.Box()
            for w in widgets[i : i + 2]:
                parent = w.get_parent()
                if parent:
                    parent.remove(w)

                row.append(w)
            self.append(row)

            for w in row.get_child():
                if w is self.wifi_widget:
                    self.append(self.wifi_widget.popup)
                elif w is self.power_profiles_widget:
                    self.append(self.power_profiles_widget.popup)
                elif w is self.bluetooth_widget:
                    self.append(self.bluetooth_widget.popup)
                elif w is self.ethernet_widget:
                    self.append(self.ethernet_widget.popup)
