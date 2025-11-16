from ignis.widgets import Widget
from ignis.services.system_tray import SystemTrayItem


class SystemTrayApp(Widget.CenterBox):
    def __init__(self, item: SystemTrayItem):
        self.item = item
        self.menu = item.menu.copy() if item.menu else None
        self.icon = self._normalize_icon(item.icon)
        self.title = self._guess_title(item)

        start_widget = Widget.Box(
            child=[
                Widget.Icon(
                    image=self.item.bind("icon") if self.icon == self.item.icon else self.icon,
                    pixel_size=28,
                    css_classes=["system-tray-item-icon"]
                ),
                Widget.Label(
                    label=self.item.bind_many(
                        ["title", "tooltip"],
                        lambda title, tooltip: title if title else tooltip if tooltip else ""
                    ) if self.title == self.item.title else self.title,
                    css_classes=["system-tray-item-label"]
                ),
            ]
        )

        if self.menu:
            self.button = Widget.Button(
                child=Widget.Icon(image="view-more-symbolic"),
                css_classes=["system-tray-item-button"],
                on_click=lambda _: self.menu.popup() if self.menu else None,
            )
            self.menu.connect("notify::visible", lambda *_: self._set_button_active(self.menu.is_visible())) # type: ignore
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

    def _guess_title(self, item: SystemTrayItem):
        if item.id == "chrome_status_icon_1" and \
           getattr(item.menu, "object_path", None) == "/com/canonical/dbusmenu" and \
           not item.title and not item.tooltip and \
           type(item.icon).__name__ == "Pixbuf":
            return "Discord"
        return item.title

    def _set_button_active(self, active: bool):
        if hasattr(self, "button"):
            self.button.css_classes = ["system-tray-item-button", "active" if active else ""]
