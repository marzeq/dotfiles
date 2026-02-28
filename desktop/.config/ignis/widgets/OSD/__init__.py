from ignis.utils import Utils
from ignis.widgets import Widget
from ignis.services.audio import AudioService


import util


audio = AudioService.get_default()


class OSD(Widget.RevealerWindow):
    def __init__(self):
        scale =  Widget.Scale(
            hexpand=True,
            min=0,
            max=100,
            step=1,
            value=audio.speaker.bind_many(  # type: ignore
                ["volume", "is_muted"],
                lambda volume, is_muted: 0 if is_muted else volume,
            ),
            css_classes=["osd-audio-slider"],
        )

        scale.connect("change-value", lambda *_: True) # prevent dragging the slider to change the valu

        revealer = Widget.Revealer(
            transition_type="slide_up",
            child=Widget.Box(
                css_classes=["osd", "runset"],
                child=[
                    Widget.Icon(
                        style="margin-right: 0.5rem;",
                        image=audio.speaker.bind(  # type: ignore
                            "icon_name",
                            lambda icon: icon
                            if icon != "image-missing"
                            else "audio-volume-muted-symbolic",
                        ),
                        css_classes=["osd-audio-icon"],
                    ),
                    scale,
                ],
            ),
            transition_duration=util.popup_manager.popup_anim_speed,
            reveal_child=True,
        )

        super().__init__(
            namespace="ignis_osd",
            layer="overlay",
            anchor=["bottom"],
            css_classes=["window"],
            visible=False,
            popup=True,
            child=Widget.Box(child=[revealer]),
            revealer=revealer,
            monitor=0,
        )

    def set_property(self, prop_name, value):
        if prop_name == "visible":
            self.__update_visible()

        super().set_property(prop_name, value)

    @Utils.debounce(3000)  # type: ignore
    def __update_visible(self) -> None:
        super().set_property("visible", False)
