from ignis.app import IgnisApp
from ignis.services.system_tray import SystemTrayItem, SystemTrayService
from ignis.services.network import NetworkService
from ignis.services.audio import AudioService
from ignis.widgets import Widget

app = IgnisApp.get_default()
system_tray = SystemTrayService.get_default()
network = NetworkService.get_default()
audio = AudioService.get_default()

def TrayItem(item: SystemTrayItem) -> Widget.Button:
    if item.menu:
        menu = item.menu.copy()
    else:
        menu = None

    return Widget.Button(
        child=Widget.Box(
            child=[
                Widget.Icon(image=item.bind("icon"), pixel_size=16),
                menu,
            ]
        ),
        setup=lambda self: item.connect("removed", lambda _: self.unparent()),
        tooltip_text=item.bind("tooltip"),
        on_click=lambda _: menu.popup() if menu else None,
        on_right_click=lambda _: menu.popup() if menu else None,
        css_classes=["tray-item"],
    )

def Tray():
    network_icon = Widget.Icon(
        css_classes=["tray-icon"],
        image="network-wired-disconnected-symbolic"
    )

    def update_network_icon():
        if network.ethernet.is_connected:
            network_icon.image = "network-wired-symbolic" # type: ignore
        elif network.wifi.is_connected:
            network_icon.image = "network-wireless-symbolic" # type: ignore
        else:
            network_icon.image = "network-wired-disconnected-symbolic" # type: ignore

    network.ethernet.connect("notify::is-connected", lambda ethernet, _: update_network_icon())
    network.wifi.connect("notify::is-connected", lambda wifi, _: update_network_icon())

    return Widget.Button(
        css_classes=["tray"],
        child=Widget.Box(child=[
            network_icon,
            Widget.Icon(
                css_classes=["tray-icon"],
                image=audio.speaker.bind( # type: ignore
                    "icon_name", lambda icon: icon if icon != "image-missing" else "audio-volume-muted-symbolic" # type: ignore
                ),
            ),
            Widget.Icon(
                css_classes=["tray-icon"],
                image="system-shutdown-symbolic"
            )
        ], css_classes=["box"]),
        on_click=lambda _: app.toggle_window("ignis_control_centre") or app.close_window("ignis_notifs_calendar"),
    )

