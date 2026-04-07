from typing import Any, Callable
from ignis.services.notifications import NotificationService
from ignis.services.mpris import MprisPlayer, MprisService
from ignis.widgets import Widget
from widgets.Notification import NotificationWidget
from ignis.gobject import Binding
import asyncio

mpris = MprisService.get_default()
notifications = NotificationService.get_default()


class PlayerControlButton(Widget.Button):
    def __init__(
        self,
        icon: str | Binding,
        on_click: Callable[[], Any],
        enabled: bool | Binding = True,
    ):
        super().__init__(
            child=Widget.Icon(
                image=icon,
                pixel_size=16,
                css_classes=["nc-player-control-icon"]
                + (["disabled"] if not enabled else []),
            ),
            css_classes=["nc-player-control-button"]
            + (["disabled"] if not enabled else []),
            on_click=lambda *_: on_click(),
            sensitive=enabled,
        )


class PlayerWidget(Widget.CenterBox):
    def __init__(self, player: MprisPlayer):
        if not player.artist and not player.title:
            super().__init__()
            return

        super().__init__(
            css_classes=["nc-player"],
            start_widget=Widget.Box(
                child=[
                    Widget.Icon(
                        image=player.bind("art_url"),
                        css_classes=["nc-player-icon"],
                        pixel_size=48,
                        visible=player.bind("art_url", lambda url: bool(url)),
                    ),
                    Widget.Box(
                        vertical=True,
                        valign="center",
                        child=[
                            Widget.Label(
                                label=player.bind("title"),
                                css_classes=["nc-player-title"],
                                halign="start",
                                ellipsize="end",
                            ),
                            Widget.Label(
                                label=player.bind("artist"),
                                css_classes=["nc-player-artist"],
                                halign="start",
                                ellipsize="end",
                            ),
                        ],
                    ),
                ]
            ),
            end_widget=Widget.Box(
                css_classes=["nc-player-controls"],
                child=[
                    PlayerControlButton(
                        icon="media-skip-backward-symbolic",
                        on_click=lambda: asyncio.create_task(player.previous_async()),
                        enabled=player.bind("can_go_previous"),
                    ),
                    PlayerControlButton(
                        icon=player.bind(
                            "playback_status",
                            lambda s: "media-playback-pause-symbolic"
                            if s == "Playing"
                            else "media-playback-start-symbolic",
                        ),
                        on_click=lambda: asyncio.create_task(player.play_pause_async()),
                    ),
                    PlayerControlButton(
                        icon="media-skip-forward-symbolic",
                        on_click=lambda: asyncio.create_task(player.next_async()),
                        enabled=player.bind("can_go_next"),
                    ),
                ],
            ),
        )


class Notifications(Widget.Box):
    def __init__(self):
        self._calendar_visible = False
        self._notif_widgets: list[NotificationWidget] = []

        super().__init__(
            css_classes=["nc-notifications"],
        )
        self.set_child([])

        def on_changed(*_):
            if self._calendar_visible:
                self._update_body()

        notifications.connect("notify::notifications", on_changed)
        notifications.connect("notify::popups", on_changed)
        mpris.connect("notify::players", on_changed)

        self._refresh_task: asyncio.Task[None] = asyncio.create_task(
            self._refresh_loop()
        )

    async def _refresh_loop(self):
        try:
            while True:
                if self._calendar_visible:
                    self._update_body()
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            return

    def set_calendar_visible(self, visible: bool) -> None:
        if self._calendar_visible == visible:
            return

        self._calendar_visible = visible
        if visible:
            self._update_body()
            return

        self._release_media()
        self.set_child([])

    def destroy(self):
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
        self._release_media()
        self.set_child([])

        parent_destroy = getattr(super(), "destroy", None)
        if callable(parent_destroy):
            parent_destroy()

    def _update_body(self):
        self._release_media()
        notifs = notifications.notifications
        notif_widgets = [NotificationWidget(n, show_time=True) for n in notifs]
        self._notif_widgets = notif_widgets

        self.set_child(
            [
                Widget.Overlay(
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
                    ]
                    if not notifs and not mpris.players
                    else [
                        Widget.Scroll(
                            child=Widget.Box(
                                vertical=True,
                                child=[PlayerWidget(p) for p in mpris.players]
                                + notif_widgets,
                            ),
                            css_classes=["nc-notifications-scroll"],
                        )
                    ],
                    hexpand=True,
                )
            ]
        )

    def _release_media(self) -> None:
        for widget in self._notif_widgets:
            widget.release_media()
        self._notif_widgets = []
