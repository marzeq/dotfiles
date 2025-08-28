from ignis.app import IgnisApp
from ignis.widgets import Widget
from ignis.services.audio import AudioService
from ignis.services.system_tray import SystemTrayService, SystemTrayItem
from ignis.services.upower import UPowerService
from ignis.services.backlight import BacklightService
from gi.repository import Gtk  # type: ignore
import utils
from widgets.bar.ControlCentre.main_widgets import MainWidgets
from widgets.bar.ControlCentre.topbox import TopBox
from widgets.bar.ControlCentre.widget import ControlCentrePopup


system_tray = SystemTrayService.get_default()
app = IgnisApp.get_default()
audio = AudioService.get_default()
upower = UPowerService.get_default()
backlight = BacklightService.get_default()

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
    def adjust_volume(x: int):
        if x > 0:
            audio.speaker.is_muted = False # type: ignore
            audio.speaker.set_volume(x) # type: ignore
        else:
            audio.speaker.is_muted = True # type: ignore

    def toggle_mute():
        audio.speaker.is_muted = not audio.speaker.is_muted # type: ignore

    power_menu = ControlCentrePopup(
        Widget.Box(
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
                        css_classes=["cc-popup-opt-label"],
                    ),
                    css_classes=["cc-popup-option"],
                    on_click=lambda _: power_menu.toggle() or utils.run_cmd_and_run("systemctl suspend", lambda: utils.close_curr_popup()),
                ),
                Widget.Button(
                    child=Widget.Label(
                        label="Restart",
                        halign="start",
                        css_classes=["cc-popup-opt-label"],
                    ),
                    css_classes=["cc-popup-option"],
                    on_click=lambda _: power_menu.toggle() or utils.run_cmd_and_run("systemctl reboot", lambda: utils.close_curr_popup()),
                ),
                Widget.Button(
                    child=Widget.Label(
                        label="Power Off",
                        halign="start",
                        css_classes=["cc-popup-opt-label"],
                    ),
                    css_classes=["cc-popup-option"],
                    on_click=lambda _: power_menu.toggle() or utils.run_cmd_and_run("systemctl poweroff", lambda: utils.close_curr_popup()),
                ),
                Widget.Button(
                    child=Widget.Label(
                        label="Log Out",
                        halign="start",
                        css_classes=["cc-popup-opt-label"],
                    ),
                    css_classes=["cc-popup-option"],
                    on_click=lambda _: power_menu.toggle() or utils.run_cmd_and_run("hyprctl dispatch exit", lambda: utils.close_curr_popup()),
                ),
            ],
        ),
        more_margin=True,
    )

    main_widgets, close_wifi_popup = MainWidgets()

    box = Widget.Box(
        vertical=True,
        css_classes=["control-centre"],
        child=[
            TopBox(lambda: power_menu.toggle()),
            power_menu,
            Widget.Box(
                css_classes=["runset", "control-centre-slider"],
                child=[
                    Widget.Button(
                        child=Widget.Icon(
                            image=audio.speaker.bind( # type: ignore
                                "icon_name", lambda icon: icon if icon != "image-missing" else "audio-volume-muted-symbolic" # type: ignore
                            ),
                        ),
                        on_click=lambda _: toggle_mute(),
                        css_classes=["cc-slider-icon"],
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
                        css_classes=["cc-slider-slider"],
                    )
                ],
            ),
        ] + ([
            Widget.Box(
                css_classes=["runset", "control-centre-slider"],
                child=[
                    Widget.Button(
                        child=Widget.Icon(
                            image="display-brightness-symbolic"
                        ),
                        css_classes=["cc-slider-icon"],
                    ),
                    Widget.Scale(
                        hexpand=True,
                        min=20,
                        max=backlight.max_brightness,
                        step=1,
                        value=backlight.devices[0].bind( # type: ignore
                            "brightness"
                        ),
                        on_change=lambda x: backlight.devices[0].set_brightness(x.value), # type: ignore
                        css_classes=["cc-slider-slider"],
                    )
                ],
            ),
        ] if backlight.available and backlight.devices else []) + [
            main_widgets,
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
        css_classes=["window"],
        namespace=f"ignis_control_centre_{monitor}",
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

    def close_popups():
        close_wifi_popup()
        power_menu.set_reveal_child(False)

    window.connect("notify::visible", lambda *_: close_popups() if window.visible else None)
    key_controller = Gtk.EventControllerKey()
    window.add_controller(key_controller)
    key_controller.connect("key-pressed", lambda *x: utils.clear_popupers() or utils.reset_popup() if x[1] == 65307 else None)  # 65307 = ESC

    return window

