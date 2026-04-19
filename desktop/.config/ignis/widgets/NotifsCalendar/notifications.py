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

        self.picture = Widget.Icon(
            image=player.bind("art_url"),
            css_classes=["nc-player-icon"],
            pixel_size=48,
            visible=player.bind("art_url", lambda url: bool(url)),
        ) 

        super().__init__(
            css_classes=["nc-player"],
            start_widget=Widget.Box(
                child=[
                    self.picture,
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

    def cleanup_image(self):
        if self.picture is not None:
            try:
                self.picture.set_property("image", "")
            except Exception:
                self.picture.image = ""
            unparent = getattr(self.picture, "unparent", None)
            if callable(unparent):
                try:
                    unparent()
                except Exception:
                    pass
            self.picture = None
        self.icon = None


class Notifications(Widget.Box):
    def __init__(self):
        self._calendar_visible = False
        self.notif_widgets: list[NotificationWidget] = []
        self.mpris_widgets: list[PlayerWidget] = []

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

        self.set_child([])

    def _update_body(self):
        notifs = notifications.notifications
        for widget in self.notif_widgets:
            widget.cleanup_image()
        for widget in self.mpris_widgets:
            widget.cleanup_image()
        self.notif_widgets = [NotificationWidget(n, show_time=True) for n in notifs]
        self.mpris_widgets = [PlayerWidget(p) for p in mpris.players if p.artist or p.title]

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
                    if not notifs and not self.mpris_widgets
                    else [
                        Widget.Scroll(
                            child=Widget.Box(
                                vertical=True,
                                child=self.mpris_widgets + self.notif_widgets,
                            ),
                            css_classes=["nc-notifications-scroll"],
                        )
                    ],
                    hexpand=True,
                )
            ]
        )
