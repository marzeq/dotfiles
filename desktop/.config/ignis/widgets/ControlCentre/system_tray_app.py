from ignis.widgets import Widget
from ignis.services.system_tray import SystemTrayItem


class SystemTrayApp(Widget.CenterBox):
    def __init__(self, item: SystemTrayItem):
        self.item = item
        self.menu = item.menu.copy() if item.menu else None
        self.title = self._normalize_title(item)

        start_widget = Widget.Box(
            child=[
                Widget.Icon(
                    image=self.item.bind("icon", lambda *_: self._normalize_icon(item.icon)),
                    pixel_size=28,
                    css_classes=["system-tray-item-icon"],
                ),
                Widget.Label(
                    label=self.item.bind("title", lambda *_: self._normalize_title(item)),
                    css_classes=["system-tray-item-label"],
                ),
            ]
        )

        if self.menu:
            self.button = Widget.Button(
                child=Widget.Icon(image="view-more-symbolic"),
                css_classes=["system-tray-item-button"],
                on_click=lambda _: self.menu.popup() if self.menu else None,
            )
            self.menu.connect(
                "notify::visible",
                lambda *_: self._set_button_active(self.menu.is_visible()), # type: ignore
            )
            end_widget = Widget.Box(child=[self.menu, self.button])
        else:
            end_widget = Widget.Box(child=[])

        super().__init__(
            start_widget=start_widget,
            end_widget=end_widget,
            setup=lambda self: self.item.connect("removed", lambda _: self.unparent()),
            css_classes=["system-tray-item"],
        )

    def _normalize_icon(self, icon):
        if isinstance(icon, str) and "spotify" in icon:
            return "spotify-client"
        return icon

    def _normalize_title(self, item: SystemTrayItem):
        if item.title == "":
            return "-"

        return item.title.capitalize()

    def _set_button_active(self, active: bool):
        if hasattr(self, "button"):
            self.button.css_classes = [
                "system-tray-item-button",
                "active" if active else "",
            ]
