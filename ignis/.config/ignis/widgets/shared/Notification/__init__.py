import time
from ignis.services.notifications import Notification
from ignis.services.applications import ApplicationsService
from ignis.widgets import Widget

applications = ApplicationsService.get_default()

def time_ago(timestamp: float) -> str:
    diff = int(time.time() - timestamp)

    if diff < 60:
        return "Just now"
    elif diff < 3600:
        minutes = diff // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < 86400:
        hours = diff // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < 2592000:
        days = diff // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif diff < 31536000:
        months = diff // 2592000
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = diff // 31536000
        return f"{years} year{'s' if years != 1 else ''} ago"

def NotificationWidget(notification: Notification, show_time: bool) -> Widget.Box:
    def set_box_classes(box: Widget.Box, classes: list[str]) -> None:
        box.css_classes = classes

    close_hovered = False
    def set_close_hovered(value: bool) -> None:
        nonlocal close_hovered
        close_hovered = value

    icon = notification.icon
    if not icon:
        if notification.app_name in applications.apps:
            icon = applications.apps[notification.app_name].icon
        else:
            searched = applications.search(applications.apps, notification.app_name)
            if searched:
                icon = searched[0].icon if searched else None

    box = Widget.EventBox(
        vertical=True,
        css_classes=["notification"],
        child=[
            Widget.CenterBox(
                start_widget=Widget.Box(
                    child=[
                        Widget.Label(
                            label=notification.app_name if notification.app_name else "Unknown App",
                            css_classes=["notification-app-name"],
                            valign="start",
                        ),
                    ] + ([Widget.Label(
                            label=time_ago(notification.time) if notification.time else "Unknown Time",
                            css_classes=["notification-time"],
                            valign="start",
                        )] if show_time else [])
                ),
                end_widget=Widget.EventBox(
                    child=[
                        Widget.Button(
                            child=Widget.Icon(image="window-close-symbolic"),
                            css_classes=["notification-button"],
                        ),
                    ],
                    on_hover=lambda _: set_box_classes(box, ["notification", "notification-close-hovered"]) or set_close_hovered(True),
                    on_hover_lost=lambda _: set_box_classes(box, ["notification"]) or set_close_hovered(False),
                ),
            ),
            Widget.Box(
                child=
                    ([Widget.Icon(
                        image=icon,
                        css_classes=["notification-icon"],
                        pixel_size=48,
                    )] if icon else []) +
                    [Widget.Box(
                        vertical=True,
                        child=[
                            Widget.Label(
                                label=notification.summary,
                                css_classes=["notification-summary"],
                                ellipsize="end",
                                halign="start",
                            ),
                        ] + (
                            [Widget.Label(
                                label=(notification.body).replace("\n", " "),
                                css_classes=["notification-body"],
                                halign="start",
                                ellipsize="end",
                            )] if notification.body else [])
                    )],
                css_classes=["notification-content"],
            )
        ],
        on_click=lambda _: (notification.actions[0].invoke() or notification.close() if notification.actions else None) if not close_hovered else
            notification.close()
    )

    return box
