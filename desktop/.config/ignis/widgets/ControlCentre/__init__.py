from ignis.widgets import Widget
from ignis.services.audio import AudioService
from ignis.services.system_tray import SystemTrayService
from ignis.services.upower import UPowerService
from ignis.services.backlight import BacklightService
from gi.repository import Gtk # pyright: ignore[reportMissingModuleSource]
import util
from widgets.ControlCentre.popup_registry import popup_registry
from widgets.ControlCentre.brightness_slider import BrightnessSlider
from widgets.ControlCentre.main_widgets import MainWidgets
from widgets.ControlCentre.power_menu import PowerMenu
from widgets.ControlCentre.system_tray_app import SystemTrayApp
from widgets.ControlCentre.topbox import TopBox
from widgets.ControlCentre.volume_slider import VolumeSlider


system_tray = SystemTrayService.get_default()
app = util.get_app()
audio = AudioService.get_default()
upower = UPowerService.get_default()
backlight = BacklightService.get_default()


class ControlCentre(Widget.RevealerWindow):
    def __init__(self, monitor: int):
        self.main_widgets = MainWidgets()
        self.power_menu = PowerMenu()
        self.volume_slider = VolumeSlider()

        def setup_tray_box(box_widget: Widget.Box):
            def on_tray_item_added(_, item):
                box_widget.append(SystemTrayApp(item))

            system_tray.connect("added", on_tray_item_added)

        box = Widget.Box(
            vertical=True,
            css_classes=["control-centre"],
            child=[
                TopBox(self.power_menu, self),
                self.power_menu,
                self.volume_slider,
                self.volume_slider.popup,
            ]
            + (
                [BrightnessSlider()]
                if backlight.available and backlight.devices
                else []
            )
            + [
                self.main_widgets,
                Widget.Box(
                    vertical=True,
                    css_classes=["control-centre-tray-items"],
                    setup=setup_tray_box,
                ),
            ],
        )

        revealer = Widget.Revealer(
            transition_type="slide_down",
            child=Widget.Box(
                vertical=True,
                css_classes=["control-centre-container"],
                child=[box],
            ),
            transition_duration=util.popup_manager.popup_anim_speed,
            reveal_child=True,
        )

        super().__init__(
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
                    on_click=lambda _: util.popup_manager.close_curr_popup(),
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

        self.connect(
            "notify::visible",
            lambda *_: popup_registry.close_all() if self.visible else None,
        )

        key_controller = Gtk.EventControllerKey()
        self.add_controller(key_controller)
        key_controller.connect(
            "key-pressed",
            lambda *x: util.popup_manager.clear_popupers()
            or util.popup_manager.reset_popup()
            if x[1] == 65307
            else None,  # 65307 = ESC
        )
