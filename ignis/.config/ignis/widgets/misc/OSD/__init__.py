from ignis.utils import Utils
from ignis.widgets import Widget
from ignis.services.audio import AudioService

audio = AudioService.get_default()

class OSD(Widget.Window):
    def __init__(self):
        super().__init__(
            namespace="ignis_osd",
            layer="overlay",
            anchor=["bottom"],
            css_classes=["runset"],
            visible=False,
            child=Widget.Box(
                css_classes=["osd"],
                child=[
                    Widget.Icon(
                        style="margin-right: 0.5rem;",
                        image=audio.speaker.bind( # type: ignore
                            "icon_name", lambda icon: icon if icon != "image-missing" else "audio-volume-muted-symbolic"
                        ),
                        css_classes=["osd-audio-icon"]
                    ),
                    Widget.Scale(
                        hexpand=True,
                        min=0,
                        max=100,
                        step=1,
                        value=audio.speaker.bind_many( # type: ignore
                            ["volume", "is_muted"],
                            lambda volume, is_muted: 0 if is_muted else volume
                        ),
                        css_classes=["osd-audio-slider"],
                    )
                ],
            ),
            monitor=0
        )

    def set_property(self, property_name, value):
        if property_name == "visible":
            self.__update_visible()

        super().set_property(property_name, value)

    @Utils.debounce(3000) # type: ignore
    def __update_visible(self) -> None:
        super().set_property("visible", False)

