import asyncio
from ignis.services.bluetooth import BluetoothService
from ignis.services.network import NetworkService, WifiAccessPoint
from ignis.widgets import Widget
from ignis.options import options

import utils
from widgets.bar.ControlCentre.widget import CCWLabels, ControlCentrePopup, ControlCentreWidget
from services.power_profiles import PowerProfilesService


network = NetworkService.get_default()
bluetooth = BluetoothService.get_default()
power_profiles = PowerProfilesService.get_default()

def WiFiPopup():
    dev = network.wifi.devices[0] if network.wifi.devices else None
    if dev is None:
        return ControlCentrePopup(Widget.Box())

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


    wants_see_more = False

    def render_networks(aps: list[WifiAccessPoint]):
        filtered = pick_strongest_aps_for_each_ssid(aps)
        if not wants_see_more:
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
                on_click=lambda _, ap=ap: utils.close_curr_popup() or asyncio.create_task(ap.connect_to_graphical()),
                css_classes=["cc-popup-option"],
            )
            for ap in filtered
        ]

        if len(filtered) < len(aps):
            widgets.append(
                Widget.Button(
                    label="See more networks" if not wants_see_more else "See fewer networks",
                    on_click=lambda _: toggle_see_more(),
                    css_classes=["cc-popup-option"],
                )
            )

        return widgets or [
            Widget.Label(label="No Wi-Fi networks found", css_classes=["cc-popup-no-wifi"])
        ]

    aps_box = Widget.Box(
        vertical=True,
        child=dev.bind("access_points", transform=render_networks)
    )

    popup = ControlCentrePopup(
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
                aps_box
            ]
        )
    )

    def toggle_see_more():
        nonlocal wants_see_more
        wants_see_more = not wants_see_more
        
        aps_box.child = render_networks(dev.access_points) # type: ignore

    return popup

def PowerProfilesPopup():
    def set_power_profile(name: str):
        power_profiles.active_profile = name # type: ignore
        popup.toggle()

    def PowerProfileButton(name: str):
        label: str
        icon: str
        if name == "performance":
            label = "Performance"
            icon = "power-profile-performance-symbolic"
        elif name == "balanced":
            label = "Balanced"
            icon = "power-profile-balanced-symbolic"
        elif name == "power-saver":
            label = "Power Saver"
            icon = "power-profile-power-saver-symbolic"
        else: return None

        return Widget.Button(
            child=Widget.Box(
                child=[
                    Widget.Icon(
                        image=icon,
                        pixel_size=18,
                        css_classes=["cc-popup-opt-icon"]
                    ),
                    Widget.Label(label=label),
                ],
                css_classes=["cc-popup-opt-label"]
            ),
            on_click=lambda _: set_power_profile(name),
            css_classes=["cc-popup-option"],
        )

    popup = ControlCentrePopup(
        Widget.Box(
            vertical=True,
            child=[
                Widget.Box(
                    child=[
                        Widget.Icon(
                            image="power-profile-balanced-symbolic",
                            css_classes=["cc-popup-icon"],
                            pixel_size=24,
                        ),
                        Widget.Label(
                            label="Power Mode",
                            css_classes=["cc-popup-label"]
                        ),
                    ],
                    css_classes=["cc-popup-header"],
                    halign="start",
                ),
                Widget.Box(
                    vertical=True,
                    child=power_profiles.bind("profiles", lambda ps: [ppb for ppb in [PowerProfileButton(p) for p in ps] if ppb is not None][::-1])
                )
            ]
        )
    )

    return popup

class MainWidgets(Widget.Box):
    def __init__(self):
        super().__init__(
            css_classes=["control-centre-widgets"],
            vertical=True,
            child=[],
        )

        self.ethernet_widget = ControlCentreWidget(
            icon=network.ethernet.bind("icon_name"),
            labels=CCWLabels("Wired"),
            on_click=lambda _: utils.run_cmd((
                "iface=$(nmcli -t -f DEVICE,TYPE,STATE device | awk -F':' '$2==\"ethernet\"{print $1; exit}'); "
                "state=$(nmcli -t -f DEVICE,STATE device | grep \"^$iface\" | cut -d':' -f2); "
                "[ $state = connected ] && "
                "nmcli device disconnect $iface || "
                "nmcli device connect $iface"
            )),
            on_click_other=lambda _: utils.run_cmd_and_run("nm-connection-editor", lambda: utils.close_curr_popup()),
        )
        network.ethernet.connect("notify::is-connected", lambda *_: self.ethernet_widget.set_disabled(not network.ethernet.is_connected))
        network.ethernet.connect("notify::devices", lambda *_: self.update_widgets())

        self.wifi_widget = ControlCentreWidget(
            icon=network.wifi.bind("icon_name"),
            labels=network.wifi.devices[0].bind_many(["is_connected", "ap"], lambda is_connected, ap: CCWLabels("Wi-Fi", ap.ssid) if is_connected and ap else CCWLabels("Wi-Fi")) if network.wifi.devices else CCWLabels("Wi-Fi"),
            on_click=lambda _: network.wifi.set_enabled(False) if network.wifi.enabled else network.wifi.set_enabled(True),
            on_click_other=lambda _: self.wifi_popup.toggle(),
        )
        network.wifi.connect("notify::enabled", lambda *_: self.wifi_widget.set_disabled(not network.wifi.enabled))
        self.wifi_popup = WiFiPopup()

        self.bluetooth_widget = ControlCentreWidget(
            icon=bluetooth.bind(
                "state",
                lambda state: "bluetooth-active-symbolic" if state == "on" and bluetooth.powered else "bluetooth-disabled-symbolic"
            ),
            labels=CCWLabels("Bluetooth"),
            on_click=lambda _: bluetooth.set_powered(False) if bluetooth.powered else bluetooth.set_powered(True),
            on_click_other=lambda _: utils.run_cmd_and_run("blueberry", lambda: utils.close_curr_popup()),
        )
        bluetooth.connect("notify::state", lambda *_: self.bluetooth_widget.set_disabled(bluetooth.state == "absent" or not bluetooth.powered))
        bluetooth.connect("notify::powered", lambda *_: self.bluetooth_widget.set_disabled(bluetooth.state == "absent" or not bluetooth.powered))
        bluetooth.connect("notify::state", lambda *_: self.update_widgets())

        def transform_pp_name(p: str) -> str:
            if p == "performance": return "Performance"
            if p == "balanced": return "Balanced"
            if p == "power-saver": return "Power Saver"
            return "Unknown"

        def set_power_profile(name: str):
            power_profiles.active_profile = name # type: ignore

        self.power_profiles_widget = ControlCentreWidget(
            icon=power_profiles.bind("icon_name"),
            labels=power_profiles.bind("active-profile", lambda p: CCWLabels("Power Mode", transform_pp_name(p)) if p else CCWLabels("Power Mode")),
            on_click=lambda _: self.power_profiles_popup.toggle() if power_profiles.active_profile == "balanced" else set_power_profile("balanced"),
            on_click_other=lambda _: self.power_profiles_popup.toggle(),
        )
        power_profiles.connect("notify::active-profile", lambda *_: self.power_profiles_widget.set_disabled(power_profiles.active_profile == "balanced"))
        power_profiles.connect("notify::is-available", lambda *_: self.update_widgets())
        self.power_profiles_popup = PowerProfilesPopup()

        self.dnd_widget = ControlCentreWidget(
            icon=options.notifications.bind("dnd", lambda dnd: "notifications-disabled-symbolic" if dnd else "org.gnome.Settings-notifications-symbolic"), # type: ignore
            labels=CCWLabels("Do Not Disturb"),
            on_click=lambda _: options.notifications.set_dnd(not options.notifications.dnd), # type: ignore
        )
        options.notifications.connect("changed", lambda _, name: None if name != "dnd" else self.dnd_widget.set_disabled(not options.notifications.dnd)) # type: ignore

        self.rows: list[Widget.Box] = []

        self.update_widgets()

    def update_widgets(self):
        self.child = [] # type: ignore
        self.rows.clear()

        widgets = []
        if network.ethernet.devices:
            widgets.append(self.ethernet_widget)
        if network.wifi.devices:
            widgets.append(self.wifi_widget)
        if bluetooth.state != "absent":
            widgets.append(self.bluetooth_widget)
        if power_profiles.is_available:
            widgets.append(self.power_profiles_widget)
        widgets.append(self.dnd_widget)

        for i in range(0, len(widgets), 2):
            row = Widget.Box()
            for w in widgets[i:i+2]:
                parent = w.get_parent()
                if parent:
                    parent.remove(w)

                row.append(w)
            self.append(row)

            for w in row.child: # type: ignore
                if w is self.wifi_widget:
                    self.append(self.wifi_popup)
                elif w is self.power_profiles_widget:
                    self.append(self.power_profiles_popup)


    def close_popups(self):
        self.wifi_popup.set_reveal_child(False)
        self.power_profiles_popup.set_reveal_child(False)
