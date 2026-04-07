from typing import Any, Callable, cast
from ignis.utils import Utils
from ignis.services.notifications import Notification, NotificationService
from ignis.services.mpris import MprisPlayer, MprisService
from ignis.services.hyprland import HyprlandService
from ignis.widgets import Widget
from widgets.Notification import NotificationWidget

import util

notifications = NotificationService.get_default()
mpris = MprisService.get_default()
hyprland = HyprlandService.get_default()
track_popup_groups: dict[str, list["TrackNotification"]] = {}


def register_track_popup(notification: "TrackNotification") -> None:
    if not notification.sync_id:
        return

    refs = track_popup_groups.setdefault(notification.sync_id, [])
    refs[:] = [notif for notif in refs if not notif._dismissed]
    refs.append(notification)


def dismiss_track_group(
    sync_id: str | None,
    source: "TrackNotification | None" = None,
) -> None:
    if not sync_id:
        return

    refs = track_popup_groups.get(sync_id, [])
    alive: list[TrackNotification] = []
    for notif in refs:
        if notif._dismissed:
            continue
        if notif is source:
            continue
        notif.close(sync_group=False)
        if not notif._dismissed:
            alive.append(notif)

    if source is not None and not source._dismissed:
        alive.append(source)

    if alive:
        track_popup_groups[sync_id] = alive
    elif sync_id in track_popup_groups:
        del track_popup_groups[sync_id]


class TrackNotification:
    def __init__(
        self,
        app_name: str,
        summary: str,
        body: str = "",
        icon: str | None = None,
        sync_id: str | None = None,
    ):
        self.app_name = app_name
        self.summary = summary
        self.body = body
        self.icon = icon
        self.sync_id = sync_id
        self.time = 0.0
        self.actions: list[Any] = []
        self._dismissed = False
        self._dismissed_callbacks: list[Callable[[Any], None]] = []

        register_track_popup(self)

    def connect(self, signal_name: str, callback: Callable[[Any], None]) -> None:
        if signal_name == "dismissed":
            self._dismissed_callbacks.append(callback)

    def close(self, sync_group: bool = True) -> None:
        if self._dismissed:
            return
        self._dismissed = True
        for callback in self._dismissed_callbacks:
            callback(self)
        if sync_group:
            dismiss_track_group(self.sync_id, source=self)


class Popup(Widget.Box):
    def __init__(
        self,
        window: Widget.Window,
        notification: Notification,
        on_destroyed: Callable[[], None] | None = None,
    ):
        self.window = window
        self.notification = notification
        self.on_destroyed = on_destroyed

        widget = NotificationWidget(notification, show_time=False)
        widget.style = "min-width: 35rem;"  # type: ignore

        self.inner = Widget.Revealer(transition_type="slide_left", child=widget)
        self.outer = Widget.Revealer(transition_type="slide_down", child=self.inner)

        super().__init__(child=[self.outer], halign="center")

        def on_dismissed(_):
            self.destroy()

        self.notification.connect("dismissed", on_dismissed)

    def destroy(self):
        def box_destroy():
            self.outer.unparent()
            if self.on_destroyed:
                self.on_destroyed()

        def outer_close():
            self.outer.reveal_child = False
            Utils.Timeout(self.outer.transition_duration, box_destroy)

        self.inner.transition_type = "crossfade"
        self.inner.reveal_child = False
        Utils.Timeout(self.outer.transition_duration, outer_close)


class PopupBox(Widget.Box):
    def __init__(self, window: Widget.Window, monitor_id: int):
        self.window = window
        self.monitor_id = monitor_id
        self._last_tracks: dict[str, tuple[str, str, str]] = {}

        super().__init__(
            vertical=True,
            valign="start",
            vexpand=False,
        )

        def on_new_popup(_, notification: Notification):
            self.on_notified(notification)

        notifications.connect(
            "new_popup",
            on_new_popup,
        )

        def on_mpris_players_changed(*_):
            self._sync_track_state()

        mpris.connect("notify::players", on_mpris_players_changed)

        self._sync_track_state()
        Utils.Poll(1000, self._check_track_changes)

    def on_notified(self, notification: Notification) -> None:
        self._show_popup(notification)

    def _show_popup(self, notification: Notification) -> None:
        if not self._is_focused_monitor() or self._has_active_fullscreen_window():
            return

        self.window.visible = True
        popup = Popup(
            window=self.window,
            notification=notification,
            on_destroyed=self._on_popup_destroyed,
        )
        self.prepend(popup)
        popup.outer.reveal_child = True
        Utils.Timeout(
            popup.outer.transition_duration, popup.inner.set_reveal_child, True
        )

    def _on_popup_destroyed(self) -> None:
        self.window.visible = bool(self.child)

    def _has_active_fullscreen_window(self) -> bool:
        if not hyprland.is_available:
            return False

        monitor = next((m for m in hyprland.monitors if m.id == self.monitor_id), None)
        if monitor is None:
            return False

        workspace = hyprland.get_workspace_by_id(monitor.active_workspace_id)
        return bool(workspace and workspace.has_fullscreen)

    def _is_focused_monitor(self) -> bool:
        if not hyprland.is_available:
            return True

        return util.active_monitor() == self.monitor_id

    def _player_key(self, player: MprisPlayer) -> str:
        bus_name = getattr(player, "bus_name", None)
        if bus_name:
            return str(bus_name)
        identity = getattr(player, "identity", None)
        if identity:
            return f"identity::{identity}::{id(player)}"
        return f"player::{id(player)}"

    def _track_state(self, player: MprisPlayer) -> tuple[str, str, str]:
        return (
            (getattr(player, "title", "") or "").strip(),
            (getattr(player, "artist", "") or "").strip(),
            (getattr(player, "art_url", "") or "").strip(),
        )

    def _sync_track_state(self) -> None:
        current_keys = {self._player_key(player) for player in mpris.players}
        self._last_tracks = {
            key: value for key, value in self._last_tracks.items() if key in current_keys
        }

        for player in mpris.players:
            key = self._player_key(player)
            self._last_tracks.setdefault(key, self._track_state(player))

    def _check_track_changes(self, *_):
        current_keys: set[str] = set()

        for player in mpris.players:
            key = self._player_key(player)
            current_keys.add(key)

            new_state = self._track_state(player)
            old_state = self._last_tracks.get(key)
            self._last_tracks[key] = new_state

            if old_state is None or old_state == new_state:
                continue

            title, artist, art_url = new_state
            if not title and not artist:
                continue

            app_name = (getattr(player, "identity", "") or "Media").strip()
            popup = TrackNotification(
                app_name=app_name,
                summary=title or "Unknown title",
                body=artist,
                icon=art_url or "audio-x-generic-symbolic",
                sync_id=f"{key}|{title}|{artist}|{art_url}",
            )
            self._show_popup(cast(Notification, popup))
            Utils.Timeout(5000, popup.close)

        self._last_tracks = {
            key: value for key, value in self._last_tracks.items() if key in current_keys
        }


class NotificationPopup(Widget.Window):
    def __init__(self, monitor: int):
        super().__init__(
            anchor=["top"],
            monitor=monitor,
            namespace=f"ignis_notification_popup_{monitor}",
            visible=False,
            css_classes=["notification-popups", "window"],
            child=PopupBox(window=self, monitor_id=monitor),
            dynamic_input_region=True,
        )
