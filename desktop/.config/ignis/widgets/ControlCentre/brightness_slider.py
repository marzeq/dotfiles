from ignis.widgets import Widget
from ignis.services.backlight import BacklightService

backlight = BacklightService.get_default()


class BrightnessSlider(Widget.Box):
    def __init__(self):
        super().__init__(
            css_classes=["runset", "control-centre-slider"],
            child=[
                Widget.Button(
                    child=Widget.Icon(image="display-brightness-symbolic"),
                    css_classes=["cc-slider-icon"],
                ),
                Widget.Scale(
                    hexpand=True,
                    min=0,
                    max=backlight.max_brightness,
                    step=1,
                    value=backlight.bind("brightness"),  # type: ignore
                    on_change=lambda x: backlight.set_brightness(x.value),  # type: ignore
                    css_classes=["cc-slider-slider"],
                ),
            ],
        )
