### UNUSED - we use swww instead. Here for reference only and if needed in future.

from gi.repository import Gdk, Gtk
from ignis.widgets import Widget

from widgets.Settings.style_settings import style_settings


class Wallpaper(Widget.Window):
    def __init__(self, monitor: Gdk.Monitor, monitor_id: int):
        def WallpaperPic(path: str):
            return Widget.Picture(
                image=path,
                content_fit="cover",
                width=monitor.get_geometry().width,
                height=monitor.get_geometry().height,
            )

        self.stack = Gtk.Stack(
            transition_type=Gtk.StackTransitionType.SLIDE_LEFT, transition_duration=250
        )
        self.stack.add_named(WallpaperPic(style_settings.wallpaper), "current")
        self.stack.add_named(WallpaperPic(style_settings.wallpaper), "next")
        self.stack.set_visible_child_name("current")

        super().__init__(
            namespace=f"ignis_wallpaper_{monitor_id}",
            monitor=monitor_id,
            anchor=["left", "top", "right", "bottom"],
            layer="background",
            exclusivity="ignore",
            child=self.stack,
        )

        style_settings.connect(
            "notify::wallpaper", lambda *_: self.on_wallpaper_change()
        )

    def on_wallpaper_change(self):
        current_child_name = self.stack.get_visible_child_name()
        next_child_name = "next" if current_child_name == "current" else "current"

        next_wallpaper = style_settings.wallpaper

        next_picture = self.stack.get_child_by_name(next_child_name)
        if not isinstance(next_picture, Widget.Picture):
            return
        next_picture.set_property("image", next_wallpaper)

        self.stack.set_visible_child_name(next_child_name)
