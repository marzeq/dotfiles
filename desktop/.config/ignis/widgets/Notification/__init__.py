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


class NotificationWidget(Widget.EventBox):
    def __init__(self, notification: Notification, show_time: bool):
        self.close_hovered = False

        self.icon = notification.icon
        if not self.icon:
            if notification.app_name in applications.apps:
                self.icon = applications.apps[notification.app_name].icon
            else:
                searched = applications.search(applications.apps, notification.app_name)
                if searched:
                    self.icon = searched[0].icon if searched else None

        super().__init__(
            vertical=True,
            css_classes=["notification"],
            child=[
                Widget.CenterBox(
                    start_widget=Widget.Box(
                        child=[
                            Widget.Label(
                                label=notification.app_name
                                if notification.app_name
                                else "Unknown App",
                                css_classes=["notification-app-name"],
                                valign="start",
                            ),
                        ]
                        + (
                            [
                                Widget.Label(
                                    label=time_ago(notification.time)
                                    if notification.time
                                    else "Unknown Time",
                                    css_classes=["notification-time"],
                                    valign="start",
                                )
                            ]
                            if show_time
                            else []
                        )
                    ),
                    end_widget=Widget.EventBox(
                        child=[
                            Widget.Button(
                                child=Widget.Icon(image="window-close-symbolic"),
                                css_classes=["notification-button"],
                            ),
                        ],
                        on_hover=lambda _: self.add_css_class(
                            "notification-close-hovered"
                        )
                        or self.set_close_hovered(True),
                        on_hover_lost=lambda _: self.remove_css_class(
                            "notification-close-hovered"
                        )
                        or self.set_close_hovered(False),
                    ),
                ),
                Widget.Box(
                    child=(
                        [
                            
                            Widget.Picture(
                                image=self.icon,
                                css_classes=["notification-icon"],
                                height=48,
                                width=-1,
                                content_fit="contain",
                                vexpand=False,
                                hexpand=False,
                            )

                        ]
                        if self.icon
                        else []
                    )
                    + [
                        Widget.Box(
                            vertical=True,
                            child=[
                                Widget.Label(
                                    label=notification.summary,
                                    css_classes=["notification-summary"],
                                    ellipsize="end",
                                    halign="start",
                                ),
                            ]
                            + (
                                [
                                    Widget.Label(
                                        label=(notification.body).replace("\n", " "),
                                        css_classes=["notification-body"],
                                        halign="start",
                                        ellipsize="end",
                                    )
                                ]
                                if notification.body
                                else []
                            ),
                        )
                    ],
                    css_classes=["notification-content"],
                ),
            ],
            on_click=lambda _: (
                notification.actions[0].invoke() or notification.close()
                if notification.actions
                else None
            )
            if not self.close_hovered
            else notification.close(),
        )

    def set_close_hovered(self, value):
        self.close_hovered = value
