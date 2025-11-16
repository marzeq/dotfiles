from ignis.utils import Utils
from ignis.services.notifications import Notification, NotificationService
from ignis.widgets import Widget
from widgets.shared.Notification import NotificationWidget

notifications = NotificationService.get_default()

class Popup(Widget.Box):
    def __init__(self, window: Widget.Window, notification: Notification):
        self.window = window
        self.notification = notification

        widget = NotificationWidget(notification, show_time=False)
        widget.style = "min-width: 35rem;"  # type: ignore

        self.inner = Widget.Revealer(transition_type="slide_down", child=widget)
        self.outer = Widget.Revealer(transition_type="slide_down", child=self.inner)

        super().__init__(
            child=[self.outer],
            halign="center"
        )

        self.notification.connect("dismissed", lambda _: self.destroy())

    def destroy(self):
        def box_destroy():
            self.outer.unparent()
            if len(notifications.popups) == 0:
                self.window.visible = False

        def outer_close():
            self.outer.reveal_child = False
            Utils.Timeout(self.outer.transition_duration, box_destroy)

        self.inner.transition_type = "crossfade"
        self.inner.reveal_child = False
        Utils.Timeout(self.outer.transition_duration, outer_close)


class PopupBox(Widget.Box):
    def __init__(self, window: Widget.Window):
        self.window = window

        super().__init__(
            vertical=True,
            valign="start",
        )

        notifications.connect(
            "new_popup",
            lambda _, notification: self.on_notified(notification),
        )

    def on_notified(self, notification: Notification) -> None:
        self.window.visible = True
        popup = Popup(window=self.window, notification=notification)
        self.prepend(popup)
        popup.outer.reveal_child = True
        Utils.Timeout(
            popup.outer.transition_duration, popup.inner.set_reveal_child, True
        )


class NotificationPopup(Widget.Window):
    def __init__(self, monitor: int):
        super().__init__(
            anchor=["top", "bottom"],
            monitor=monitor,
            namespace=f"ignis_notification_popup_{monitor}",
            layer="top",
            visible=False,
            style="min-width: 35rem;",
            css_classes=["notification-popups", "window"],
            child=PopupBox(window=self),
            dynamic_input_region = True
        )
