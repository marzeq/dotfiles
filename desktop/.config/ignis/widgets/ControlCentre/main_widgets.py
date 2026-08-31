from ignis.services.bluetooth import BluetoothService
from ignis.services.network import NetworkService
from ignis.widgets import Widget
import util

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

        def on_devices_or_state(*_):
            self.update_widgets()

        network.ethernet.connect("notify::devices", on_devices_or_state)

        self.wifi_widget = WiFiWidget()
        network.wifi.connect("notify::devices", on_devices_or_state)

        self.bluetooth_widget = BluetoothWidget()
        bluetooth.connect("notify::state", on_devices_or_state)

        self.power_profiles_widget = PowerProfilesWidget()

        self.dnd_widget = DNDWidget()

        self.rows: list[Widget.Box] = []

        self.update_widgets()

    def update_widgets(self):
        # These controls and popups are long-lived and get moved between newly
        # constructed layout rows. Detach them before disposing the old row
        # containers; otherwise recursive teardown correctly treats them as
        # discarded children and permanently disposes their GTK objects.
        reusable_widgets = (
            self.ethernet_widget,
            self.ethernet_widget.popup,
            self.wifi_widget,
            self.wifi_widget.popup,
            self.bluetooth_widget,
            self.bluetooth_widget.popup,
            self.power_profiles_widget,
            self.power_profiles_widget.popup,
            self.dnd_widget,
        )
        for widget in reusable_widgets:
            if widget.get_parent() is not None:
                util.detach_widget(widget)

        util.replace_box_children(self, [])
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
