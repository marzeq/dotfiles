from gi.repository import Gdk, Graphene # type: ignore[reportMissingModuleSource]
from ignis.gobject import IgnisProperty
from ignis.widgets import Widget


class FilteredPicture(Widget.Picture):
    def __init__(
        self,
        content_fit: str = "contain",
        width: int = -1,
        height: int = -1,
        blur_radius: int = 0,
        opacity: float = 1.0,
        darken: float = 0.0,
        **kwargs,
    ):
        super().__init__(
            content_fit=content_fit,
            width=width,
            height=height,
            **kwargs,
        )
        self._blur_radius = blur_radius
        self._opacity = opacity
        self._darken = darken

    @IgnisProperty
    def blur_radius(self) -> int: # type: ignore
        return self._blur_radius

    @blur_radius.setter
    def blur_radius(self, value: int) -> None:
        self._blur_radius = value
        self.queue_draw()

    @IgnisProperty
    def opacity(self) -> float: # type: ignore
        return self._opacity

    @opacity.setter
    def opacity(self, value: float) -> None:
        self._opacity = max(0.0, min(1.0, value))
        self.queue_draw()

    @IgnisProperty
    def darken(self) -> float: # type: ignore
        return self._darken

    @darken.setter
    def darken(self, value: float) -> None:
        self._darken = max(0.0, min(1.0, value))
        self.queue_draw()

    def do_snapshot(self, snapshot):
        if self._blur_radius > 0:
            snapshot.push_blur(self._blur_radius)

        if self._opacity < 1.0:
            snapshot.push_opacity(self._opacity)

        Widget.Picture.do_snapshot(self, snapshot)

        if self._darken > 0.0:
            alloc = self.get_allocation()
            rect = Graphene.Rect().init(0, 0, alloc.width, alloc.height)
            snapshot.append_color(
                Gdk.RGBA(0, 0, 0, self._darken),
                rect,
            )

        if self._opacity < 1.0:
            snapshot.pop()

        if self._blur_radius > 0:
            snapshot.pop()
