from ignis.services.notifications import NotificationService
from ignis.utils import Utils
from ignis.widgets import Widget

from widgets.shared.Notification import NotificationWidget


notifications = NotificationService.get_default()

class Notifications(Widget.Box):
    def __init__(self):
        super().__init__(
            css_classes=["nc-notifications"],
        )
        self._update_body()

        notifications.connect("notify::notifications", lambda *_: self._update_body())
        Utils.Poll(60_000, lambda *_: self._update_body()) # to update the "X minutes ago" etc. labels

    def _update_body(self):
        notifs = notifications.notifications

        self.set_child([Widget.Overlay(
            child=Widget.Box(
                child=[
                    Widget.Button(
                        label="Clear",
                        on_click=lambda _: notifications.clear_all(),
                        css_classes=["nc-notifications-clear"],
                        sensitive=bool(len(notifs)),
                    )
                ],
                css_classes=["nc-notifications-bottom"],
                valign="end",
            ),
            overlays=[
                Widget.Box(
                    vertical=True,
                    valign="center",
                    child=[
                        Widget.Icon(
                            image="no-notifications-symbolic",
                            css_classes=["nc-notifications-empty-icon"],
                            pixel_size=96,
                        ),
                        Widget.Label(
                            label="No notifications",
                            css_classes=["nc-notifications-empty-label"],
                        ),
                    ],
                )
            ] if not notifs else [Widget.Scroll(
                child=Widget.Box(
                    vertical=True,
                    child=[NotificationWidget(n, show_time=True) for n in notifs],
                ),
                css_classes=["nc-notifications-scroll"],
            )],
            hexpand=True,
        )])
