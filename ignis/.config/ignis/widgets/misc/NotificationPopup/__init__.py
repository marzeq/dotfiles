from ignis.utils import Utils
from ignis.services.notifications import Notification, NotificationService
from ignis.widgets import Widget
from widgets.shared.Notification import NotificationWidget

notifications = NotificationService.get_default()

def Popup(window: Widget.Window, notification: Notification):
    widget = NotificationWidget(notification, show_time=False)
    widget.style = "min-width: 35rem;" # type: ignore
    inner = Widget.Revealer(transition_type="slide_down", child=widget)
    outer = Widget.Revealer(transition_type="slide_down", child=inner)

    def destroy():
        def box_destroy():
            outer.unparent()
            if len(notifications.popups) == 0:
                window.visible = False

        def outer_close():
            outer.reveal_child = False
            Utils.Timeout(outer.transition_duration, box_destroy)

        inner.transition_type = "crossfade"
        inner.reveal_child = False
        Utils.Timeout(outer.transition_duration, outer_close)

    notification.connect("dismissed", lambda _: destroy())

    return Widget.Box(child=[outer], halign="center"), inner, outer


def PopupBox(window: Widget.Window):
    def on_notified(box: Widget.Box, notification: Notification) -> None:
        window.visible = True
        popup, inner, outer = Popup(window=window, notification=notification)
        box.prepend(popup)
        outer.reveal_child = True
        Utils.Timeout(
            outer.transition_duration, inner.set_reveal_child, True
        )

    notifications.connect(
        "new_popup",
        lambda _, notification: on_notified(box, notification),
    )

    box = Widget.Box(
        vertical=True,
        valign="start",
    )

    return box


def NotificationPopup(monitor: int):
    window = Widget.Window(
        anchor=["top", "bottom"],
        monitor=monitor,
        namespace=f"ignis_notification_popup_{monitor}",
        layer="top",
        visible=False,
        style="min-width: 35rem;",
        css_classes=["runset", "notification-popups"],
    )
    window.child = PopupBox(window=window)
    window.dynamic_input_region = True

    return window
