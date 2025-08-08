from typing import Any, Callable
from ignis.app import IgnisApp
from ignis.widgets import Widget
from ignis.services.audio import AudioService
from ignis.services.network import NetworkService
from ignis.services.bluetooth import BluetoothService
from ignis.services.system_tray import SystemTrayService, SystemTrayItem
from gi.repository import Gtk  # type: ignore

system_tray = SystemTrayService.get_default()

import utils

import os

app = IgnisApp.get_default()
audio = AudioService.get_default()
network = NetworkService.get_default()
bluetooth = BluetoothService.get_default()

def ControlCentreWidget(
    icon: Widget.Icon,
    label: Widget.Label,
    on_click: Callable[..., Any] | None = None,
    on_click_other: Callable[..., Any] | None = None,
    **kwargs
) -> Widget.Grid:
    disabled: bool = kwargs.get("disabled", False)
    if on_click_other is not None:
        return Widget.Grid(
            column_num=2,
            child=[
                Widget.Button(
                    child=Widget.Box(
                        child=[icon, label],
                        css_classes=["cc-widget-left"]
                    ),
                    on_click=on_click,
                    hexpand=True,
                ),
                Widget.Button(
                    child=Widget.Icon(image="go-next-symbolic"),
                    css_classes=["cc-widget-right"],
                    on_click=on_click_other,
                ),
            ],
            css_classes=["cc-widget"] if not disabled else ["cc-widget", "cc-widget-disabled"],
        )
    else:
        return Widget.Grid(
            column_num=2,
            child=[
                Widget.Button(
                    child=Widget.Box(
                        child=[icon, label],
                        css_classes=["cc-widget-left", "cc-widget-left-full"]
                    ),
                    hexpand=True,
                    on_click=on_click,
                ),
            ],
            css_classes=["cc-widget"] if not disabled else ["cc-widget", "cc-widget-disabled"],
        )

def SystemTrayApp(item: SystemTrayItem) -> Widget.Button:
    if item.menu:
        menu = item.menu.copy()
    else:
        menu = None

    icon = item.icon
    if isinstance(icon, str) and "spotify" in icon:
        icon = "spotify-client"

    return Widget.CenterBox(
        start_widget=Widget.Box(
            child=[
                Widget.Icon(
                    image=item.bind("icon") if icon == item.icon else icon,
                    pixel_size=28,
                    css_classes=["system-tray-item-icon"]
                ),
                Widget.Label(
                    label=
                    item.bind_many(
                        ["title", "tooltip"],
                        lambda title, tooltip: title if title else tooltip if tooltip else "---"
                    ),
                    css_classes=["system-tray-item-label"]
                ),
            ],
        ),
        end_widget=Widget.Box(
            child=([
                Widget.Button(
                    child=Widget.Icon(
                        image="view-fullscreen-symbolic",
                    ),
                    css_classes=["system-tray-item-button"],
                    on_click=lambda _: item.activate() or utils.close_curr_popup(),
                )
            ]) + ([
                menu,
                Widget.Button(
                    child=Widget.Icon(
                        image="view-more-symbolic",
                    ),
                    css_classes=["system-tray-item-button"],
                    on_click=lambda _: menu.popup(),
                ),
            ] if menu else []),
        ),
        setup=lambda self: item.connect("removed", lambda _: self.unparent()),
        css_classes=["system-tray-item"],
    )

def ControlCentre(monitor: int):
    widgets = Widget.Grid(
        css_classes=["control-centre-widgets"],
        column_num=2,
        child=[],
    )

    def update_widgets():
        children = []
        if network.ethernet.devices:
            children.append(ControlCentreWidget(
                Widget.Icon(image=network.ethernet.bind("icon_name")),
                Widget.Label(label="Wired", css_classes=["cc-widget-label"]),
                lambda _: utils.run_cmd((
                        "iface=$(nmcli -t -f DEVICE,TYPE,STATE device | awk -F':' '$2==\"ethernet\"{print $1; exit}'); "
                        "state=$(nmcli -t -f DEVICE,STATE device | grep \"^$iface\" | cut -d':' -f2); "
                        "[ $state = connected ] && "
                        "nmcli device disconnect $iface || "
                        "nmcli device connect $iface"
                    )),
                lambda _: utils.run_cmd_and_run("nm-connection-editor", lambda: utils.close_curr_popup()),
                disabled=not network.ethernet.is_connected
            ))
        if network.wifi.devices:
            children.append(ControlCentreWidget(
                Widget.Icon(image=network.wifi.bind("icon_name")),
                Widget.Label(label="Wi-Fi", css_classes=["cc-widget-label"]),
                lambda _: utils.run_cmd("nmcli radio wifi off") if network.wifi.enabled else utils.run_cmd("nmcli radio wifi on"),
                lambda _: utils.run_cmd_and_run("nm-connection-editor", lambda: utils.close_curr_popup()),
                disabled=not network.wifi.enabled
            ))
        if bluetooth.state != "absent":
            children.append(ControlCentreWidget(
                Widget.Icon(image=bluetooth.bind("state", lambda state:
                    "bluetooth-active-symbolic" if state == "on" and bluetooth.powered else "bluetooth-disabled-symbolic")),
                Widget.Label(label="Bluetooth", css_classes=["cc-widget-label"]),
                lambda _: utils.run_cmd("bluetoothctl power off") if bluetooth.state == "on" else utils.run_cmd("bluetoothctl power on"),
                lambda _: utils.run_cmd_and_run("blueberry", lambda: utils.close_curr_popup()),
                disabled=bluetooth.state == "absent" or not bluetooth.powered
            )) 


        widgets.child = children # type: ignore

    update_widgets()

    network.ethernet.connect("notify::is-connected", lambda *_: update_widgets())
    network.wifi.connect("notify::is-connected", lambda *_: update_widgets())
    network.wifi.connect("notify::enabled", lambda *_: update_widgets())
    bluetooth.connect("notify::state", lambda *_: update_widgets())

    def adjust_volume(x: int):
        if x > 0:
            audio.speaker.is_muted = False # type: ignore
            audio.speaker.set_volume(x) # type: ignore
        else:
            audio.speaker.is_muted = True # type: ignore

    def toggle_mute():
        audio.speaker.is_muted = not audio.speaker.is_muted # type: ignore

    toggle_power_menu = lambda: None

    power_menu = Widget.Revealer(
        transition_type="slide_down",
        transition_duration=utils.popup_anim_speed,
        child=Widget.Box(
            vertical=True,
            child=[
                Widget.Box(
                    child=[
                        Widget.Icon(
                            image="system-shutdown-symbolic",
                            css_classes=["cc-popup-icon"],
                            pixel_size=24,
                        ),
                        Widget.Label(
                            label="Power Off",
                            css_classes=["cc-popup-label"]
                        ),
                    ],
                    css_classes=["cc-popup-header"],
                    halign="start",
                ),
                Widget.Button(
                    child=Widget.Label(
                        label="Suspend",
                        halign="start",
                        css_classes=["cc-power-menu-opt-label"],
                    ),
                    css_classes=["cc-power-menu-option"],
                    on_click=lambda _: toggle_power_menu() or utils.run_cmd_and_run("systemctl suspend", lambda: utils.close_curr_popup()),
                ),
                Widget.Button(
                    child=Widget.Label(
                        label="Restart",
                        halign="start",
                        css_classes=["cc-power-menu-opt-label"],
                    ),
                    css_classes=["cc-power-menu-option"],
                    on_click=lambda _: toggle_power_menu() or utils.run_cmd_and_run("systemctl reboot", lambda: utils.close_curr_popup()),
                ),
                Widget.Button(
                    child=Widget.Label(
                        label="Power Off",
                        halign="start",
                        css_classes=["cc-power-menu-opt-label"],
                    ),
                    css_classes=["cc-power-menu-option"],
                    on_click=lambda _: toggle_power_menu() or utils.run_cmd_and_run("systemctl poweroff", lambda: utils.close_curr_popup()),
                ),
                Widget.Button(
                    child=Widget.Label(
                        label="Log Out",
                        halign="start",
                        css_classes=["cc-power-menu-opt-label"],
                    ),
                    css_classes=["cc-power-menu-option"],
                    on_click=lambda _: toggle_power_menu() or utils.run_cmd_and_run("hyprctl dispatch exit", lambda: utils.close_curr_popup()),
                ),
            ],
            css_classes=["cc-popup"],
        )
    )

    power_menu_toggled = False
    def toggle_power_menu():
        nonlocal power_menu_toggled, power_menu

        if power_menu_toggled:
            power_menu_toggled = False
            power_menu.set_reveal_child(False) # type: ignore
            return

        power_menu_toggled = True
        power_menu.set_reveal_child(True) # type: ignore

    def force_close_power_menu():
        nonlocal power_menu_toggled
        if power_menu_toggled:
            power_menu_toggled = False
            power_menu.set_reveal_child(False) # type: ignore

    box = Widget.Box(
        vertical=True,
        css_classes=["control-centre"],
        child=[
            Widget.CenterBox(
                css_classes=["control-centre-top"],
                start_widget=Widget.Box(
                    child=[
                        Widget.Button(child=Widget.Icon(
                            image=f"screenshooter-symbolic"), # type: ignore 
                            css_classes=["cc-top-button"],
                            on_click=lambda _: utils.run_cmd_and_run_delayed("hyprshot -szm region -o ~/pictures/screenshots/", lambda: utils.close_curr_popup(), 100),
                        ),
                        Widget.Button(child=Widget.Icon(
                            image="applications-system-symbolic"),
                            css_classes=["cc-top-button"],
                            on_click=lambda _: app.open_window("ignis_settings") or utils.close_curr_popup(),
                        ),
                    ]
                ),
                end_widget=Widget.Box(
                    child=[
                        Widget.Button(child=Widget.Icon(
                            image="system-lock-screen-symbolic"),
                            css_classes=["cc-top-button"],
                            on_click=lambda _: utils.run_cmd_and_run_delayed("loginctl lock-session", lambda: utils.close_curr_popup(), 100),
                        ),
                        Widget.Button(child=Widget.Icon(
                            image="system-shutdown-symbolic"),
                            css_classes=["cc-top-button"],
                            on_click=lambda _: toggle_power_menu()
                        ),
                    ]
                )
            ),
            power_menu,
            Widget.Box(
                css_classes=["control-centre-audio"],
                child=[
                    Widget.Button(
                        child=Widget.Icon(
                            image=audio.speaker.bind( # type: ignore
                                "icon_name", lambda icon: icon if icon != "image-missing" else "audio-volume-muted-symbolic" # type: ignore
                            ),
                        ),
                        on_click=lambda _: toggle_mute(),
                        css_classes=["cc-audio-icon"],
                    ),
                    Widget.Scale(
                        hexpand=True,
                        min=0,
                        max=100,
                        step=1,
                        value=audio.speaker.bind_many( # type: ignore
                            ["volume", "is_muted"],
                            lambda volume, is_muted: 0 if is_muted else volume,
                        ),
                        on_change=lambda x: adjust_volume(x.value),
                        css_classes=["cc-audio-slider"],
                    )
                ],
            ),
            widgets,
            Widget.Box(
                vertical=True,
                css_classes=["control-centre-tray-items"],
                setup=lambda self: system_tray.connect(
                    "added", lambda _, item: self.append(SystemTrayApp(item))
                ),
            ),
        ]
    )

    revealer = Widget.Revealer(
        transition_type="slide_down",
        child=Widget.Box(
            vertical=True,
            css_classes=["control-centre-container"],
            child=[box],
        ),
        transition_duration=utils.popup_anim_speed,
        reveal_child=True,
    )

    window = Widget.RevealerWindow(
        visible=False,
        popup=True,
        kb_mode="on_demand",
        monitor=monitor,
        layer="top",
        anchor=["top", "right", "bottom", "left"],
        namespace=f"ignis_control_centre_{monitor}",
        css_classes=["runset"],
            child=Widget.Overlay(
            child=Widget.EventBox(
                vexpand=True,
                hexpand=True,
                on_click=lambda _: utils.close_curr_popup(),
            ),
            overlays=[
                Widget.Box(
                    vertical=True,
                    valign="start",
                    halign="end",
                    child=[revealer],
                ),
            ],
        ),
        revealer=revealer,
    )

    window.connect("notify::visible", lambda *_: force_close_power_menu() if window.visible and power_menu_toggled else None)
    key_controller = Gtk.EventControllerKey()
    window.add_controller(key_controller)
    key_controller.connect("key-pressed", lambda *x: utils.clear_popupers() or utils.reset_popup() if x[1] == 65307 else None)  # 65307 = ESC

    return window

