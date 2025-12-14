from ignis.widgets import Widget
import util
from widgets.ControlCentre.popup_registry import popup_registry
from widgets.ControlCentre.widget import ControlCentrePopup

class PowerMenu(ControlCentrePopup):
    def __init__(self):
        popup_registry.register(self)
        super().__init__(
            Widget.Box(
                vertical=True,
                hexpand=True,
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
                        on_click=lambda _: self.toggle() or util.run_cmd_and_run("systemctl suspend", lambda: util.popup_manager.close_curr_popup()),
                    ),
                    Widget.Button(
                        child=Widget.Label(
                            label="Restart",
                            halign="start",
                            css_classes=["cc-popup-opt-label"],
                        ),
                        css_classes=["cc-popup-option"],
                        on_click=lambda _: self.toggle() or util.run_cmd_and_run("systemctl reboot", lambda: util.popup_manager.close_curr_popup()),
                    ),
                    Widget.Button(
                        child=Widget.Label(
                            label="Power Off",
                            halign="start",
                            css_classes=["cc-popup-opt-label"],
                        ),
                        css_classes=["cc-popup-option"],
                        on_click=lambda _: self.toggle() or util.run_cmd_and_run("systemctl poweroff", lambda: util.popup_manager.close_curr_popup()),
                    ),
                    Widget.Button(
                        child=Widget.Label(
                            label="Log Out",
                            halign="start",
                            css_classes=["cc-popup-opt-label"],
                        ),
                        css_classes=["cc-popup-option"],
                        on_click=lambda _: self.toggle() or util.run_cmd_and_run("hyprctl dispatch exit", lambda: util.popup_manager.close_curr_popup()),
                    ),
                ],
            ),
            more_margin=True,
        )
