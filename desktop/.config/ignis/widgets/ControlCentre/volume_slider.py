from ignis.widgets import Widget
from ignis.services.audio import AudioService, Stream
import util
from widgets.ControlCentre.popup_registry import popup_registry
from widgets.ControlCentre.device_list_popup import DeviceListPopup

audio = AudioService.get_default()

def speaker_select(sp: Stream) -> None:
    util.run_cmd(f"pactl set-default-sink {sp.name}")

def speaker_deselect(sp: Stream) -> None:
    util.run_cmd(f"pactl set-default-sink {sp.name}")

class SpeakerPopup(DeviceListPopup[Stream]):
    def __init__(self) -> None:
        super().__init__(
            title="Sound Output",
            device=audio,
            item_key="speakers",
            icon_name_fn=lambda sp: sp.bind("icon_name"),
            label_fn=lambda sp: sp.bind("description"),
            connect_fn=speaker_select,
            disconnect_fn=speaker_deselect,
            header_icon="audio-headphones-symbolic",
            connected_property="is_default",
            connected_check=lambda is_default: is_default
        )

    def filter_items(self, items):
        default_items = [item for item in items if item.is_default]
        other_items = [item for item in items if not item.is_default]
        return default_items + other_items

class VolumeSlider(Widget.Box):
    def __init__(self):
        self.popup = SpeakerPopup()
        popup_registry.register(self.popup)

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
                    on_click=lambda _: popup_registry.close_all_but(self.popup) or self.popup.toggle(),
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
