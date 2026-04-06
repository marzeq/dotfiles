from typing import Any, Callable
import weakref
from ignis.services.notifications import NotificationService
from ignis.services.mpris import MprisPlayer, MprisService
from ignis.utils import Utils
from ignis.widgets import Widget
from widgets.Notification import NotificationWidget
from ignis.gobject import Binding
import asyncio

mpris = MprisService.get_default()
notifications = NotificationService.get_default()


class PlayerControlButton(Widget.Button):
    def __init__(self, icon: str | Binding, on_click: Callable[[], Any], enabled: bool | Binding = True):
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
        super().__init__(
            css_classes=["nc-notifications"],
        )
        self._update_body()

        weak_self = weakref.ref(self)

        def on_changed(*_):
            instance = weak_self()
            if instance is None:
                return
            instance._update_body()

        notifications.connect("notify::notifications", on_changed)
        mpris.connect("notify::players", on_changed)

        Utils.Poll(60_000, on_changed)  # refresh relative timestamps periodically

    def _update_body(self):
        notifs = notifications.notifications

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
                                + [
                                    NotificationWidget(n, show_time=True)
                                    for n in notifs
                                ],
                            ),
                            css_classes=["nc-notifications-scroll"],
                        )
                    ],
                    hexpand=True,
                )
            ]
        )
