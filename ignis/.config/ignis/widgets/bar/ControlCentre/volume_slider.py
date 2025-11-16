from ignis.widgets import Widget
from ignis.services.audio import AudioService
import util

audio = AudioService.get_default()

class VolumeSlider(Widget.Box):
    def __init__(self):
        super().__init__(
            css_classes=["runset", "control-centre-slider"],
            child=[
                Widget.Button(
                    child=Widget.Icon(
                        image=audio.speaker.bind(  # type: ignore
                            "icon_name",
                            lambda icon: icon if icon != "image-missing" else "audio-volume-muted-symbolic"
                        ),
                    ),
                    on_click=lambda _: self.toggle_mute(),
                    css_classes=["cc-slider-icon"],
                ),
                Widget.Scale(
                    hexpand=True,
                    min=0,
                    max=100,
                    step=1,
                    value=audio.speaker.bind_many(  # type: ignore
                        ["volume", "is_muted"],
                        lambda volume, is_muted: 0 if is_muted else volume
                    ),
                    on_change=lambda x: self.adjust_volume(x.value),
                    css_classes=["cc-slider-slider"],
                ),
                Widget.Button(
                    child=Widget.Icon(image="go-next-symbolic"),
                    css_classes=["cc-slider-icon"],
                    on_click=lambda _: util.run_cmd_and_run(
                        "pavucontrol",
                        lambda: util.popup_manager.close_curr_popup()
                    ),
                ),
            ]
        )

    def adjust_volume(self, x: int):
        if x > 0:
            audio.speaker.is_muted = False  # type: ignore
            audio.speaker.set_volume(x)  # type: ignore
        else:
            audio.speaker.is_muted = True  # type: ignore

    def toggle_mute(self):
        audio.speaker.is_muted = not audio.speaker.is_muted  # type: ignore
