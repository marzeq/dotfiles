from typing import Callable
from ignis.widgets import Widget
from services.power_profiles.service import PowerProfilesService
from widgets.bar.ControlCentre.popup_registry import popup_registry
from widgets.bar.ControlCentre.widget import CCWLabels, ControlCentrePopup, ControlCentreWidget

power_profiles = PowerProfilesService.get_default()

def transform_pp_name(p: str) -> str:
    if p == "performance": return "Performance"
    if p == "balanced": return "Balanced"
    if p == "power-saver": return "Power Saver"
    return "Unknown"

def set_power_profile(name: str):
    power_profiles.set_active_profile(name)

class PowerProfileButton(Widget.Button):
    def __init__(self, name: str, close_popup: Callable[[], None]):
        self.label: str
        self.icon: str

        if name == "performance":
            label = "Performance"
            icon = "power-profile-performance-symbolic"
        elif name == "balanced":
            label = "Balanced"
            icon = "power-profile-balanced-symbolic"
        elif name == "power-saver":
            label = "Power Saver"
            icon = "power-profile-power-saver-symbolic"
        else:
            return None

        super().__init__(
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
            on_click=lambda _: set_power_profile(name) or close_popup(),
            css_classes=["cc-popup-option"],
        )

class PowerProfilesPopup(ControlCentrePopup):
    def __init__(self):
        super().__init__(
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
                        child=power_profiles.bind("profiles", lambda ps: [ppb for ppb in [PowerProfileButton(p, lambda: self.toggle()) for p in ps] if ppb is not None][::-1])
                    )
                ]
            )
        )

class PowerProfilesWidget(ControlCentreWidget):
    def __init__(self):
        self.popup = PowerProfilesPopup()
        popup_registry.register(self.popup)

        super().__init__(
            icon=power_profiles.bind("icon_name"),
            labels=power_profiles.bind("active-profile", lambda p: CCWLabels("Power Mode", transform_pp_name(p)) if p else CCWLabels("Power Mode")),
            on_click=lambda _: self.popup.toggle() if power_profiles.active_profile == "balanced" else set_power_profile("balanced"),
            on_click_other=lambda _: popup_registry.close_all_but(self.popup) or self.popup.toggle(),
        )

        power_profiles.connect("notify::active-profile", lambda *_: self.set_disabled(power_profiles.active_profile == "balanced"))
        power_profiles.connect("notify::is-available", lambda *_: self.update_widgets())

    @staticmethod
    def is_available() -> bool:
        return power_profiles.is_available
