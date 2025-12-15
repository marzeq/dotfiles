from ignis.gobject import IgnisProperty
from ignis.widgets import Widget


class BlurredPicture(Widget.Picture):
    def __init__(
        self,
        content_fit: str = "contain",
        width: int = -1,
        height: int = -1,
        blur_radius: int = 0,
        **kwargs,
    ):
        super().__init__(
            content_fit=content_fit,
            width=width,
            height=height,
            **kwargs,
        )
        self._blur_radius = blur_radius

    @IgnisProperty
    def blur_radius(self) -> "int":
        """
        The radius of the blur effect applied to the picture in pixels.
        """
        return self._blur_radius

    @blur_radius.setter
    def blur_radius(self, value: "int") -> None:
        self._blur_radius = value
        self.queue_draw()

    def do_snapshot(self, snapshot):
        snapshot.push_blur(self._blur_radius)

        Widget.Picture.do_snapshot(self, snapshot)

        snapshot.pop()
