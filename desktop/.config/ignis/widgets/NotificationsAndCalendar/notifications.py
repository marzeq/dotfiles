from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from gi.repository import GdkPixbuf, GLib, Gtk  # pyright: ignore[reportMissingModuleSource]
from ignis.services.mpris import MprisPlayer, MprisService
from ignis.services.notifications import (
    NOTIFICATIONS_IMAGE_DATA,
    Notification,
    NotificationService,
)
from ignis.widgets import Widget

import util


POPUP_ANIMATION_MS = 220
SCROLL_FADE_RAMP_PX = 48
MAX_NOTIFICATION_HISTORY = 100
NOTIFICATION_IMAGE_CACHE = Path(NOTIFICATIONS_IMAGE_DATA)

notification_service = NotificationService.get_default()
mpris_service = MprisService.get_default()


def _scaled_icon(
    image: str | None,
    size: int,
    css_classes: list[str],
    fallback: str,
) -> Widget.Icon:
    """Decode file-backed images at display size instead of retaining full-size pixbufs."""
    source: str | GdkPixbuf.Pixbuf = image or fallback
    if image and Path(image).is_file():
        try:
            source = GdkPixbuf.Pixbuf.new_from_file_at_scale(image, size, size, True)
        except GLib.Error:
            source = fallback
    return Widget.Icon(image=source, pixel_size=size, css_classes=css_classes)


def _notification_age(timestamp: float) -> str:
    seconds = max(0, int(datetime.now().timestamp() - timestamp))
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86_400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = seconds // 86_400
    return f"{days} day{'s' if days != 1 else ''} ago"


def _cached_notification_image(path: str | None) -> Path | None:
    if not path:
        return None

    candidate = Path(path)
    try:
        resolved = candidate.resolve()
        resolved.relative_to(NOTIFICATION_IMAGE_CACHE.resolve())
    except (OSError, ValueError):
        return None
    return resolved if resolved.is_file() else None


class NotificationAssets:
    """Own cached notification images until all widgets have released them."""

    def __init__(self) -> None:
        self._refs: dict[int, int] = {}
        self._paths: dict[int, Path] = {}
        self._closed: set[int] = set()
        self._close_handlers: dict[int, tuple[Notification, int]] = {}
        self._clear_orphaned_images()

    def _clear_orphaned_images(self) -> None:
        if not NOTIFICATION_IMAGE_CACHE.is_dir():
            return
        live = {
            path
            for notification in notification_service.notifications
            if (path := _cached_notification_image(notification.icon)) is not None
        }
        for path in NOTIFICATION_IMAGE_CACHE.iterdir():
            if path.is_file() and path.resolve() not in live:
                try:
                    path.unlink()
                except OSError:
                    pass

    def acquire(self, notification: Notification) -> None:
        notification_id = notification.id
        self._refs[notification_id] = self._refs.get(notification_id, 0) + 1
        path = _cached_notification_image(notification.icon)
        if path is not None:
            self._paths[notification_id] = path
        if notification_id not in self._close_handlers:
            handler = notification.connect("closed", self._on_closed)
            self._close_handlers[notification_id] = (notification, handler)

    def release(self, notification_id: int) -> None:
        count = self._refs.get(notification_id, 0) - 1
        if count > 0:
            self._refs[notification_id] = count
        else:
            self._refs.pop(notification_id, None)
            self._finish(notification_id)

    def _on_closed(self, notification: Notification) -> None:
        self._closed.add(notification.id)
        self._finish(notification.id)

    def _finish(self, notification_id: int) -> None:
        if notification_id not in self._closed or notification_id in self._refs:
            return

        path = self._paths.pop(notification_id, None)
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

        tracked = self._close_handlers.pop(notification_id, None)
        if tracked is not None:
            notification, handler = tracked
            if notification.handler_is_connected(handler):
                notification.disconnect(handler)
        self._closed.discard(notification_id)


notification_assets = NotificationAssets()


def _trim_notification_history(*_args) -> None:
    """Keep notification objects and their cached assets bounded."""
    overflow = len(notification_service.notifications) - MAX_NOTIFICATION_HISTORY
    for notification in tuple(notification_service.notifications)[: max(0, overflow)]:
        notification.close()


notification_service.connect("notified", _trim_notification_history)
_trim_notification_history()


class NotificationCard(Widget.Box):
    """The shared card used by notification history and popup surfaces."""

    def __init__(
        self,
        notification: Notification,
        *,
        popup: bool,
        on_remove: Callable[["NotificationCard"], None],
    ) -> None:
        self._notification: Notification | None = notification
        self._notification_id = notification.id
        self._popup = popup
        self._on_remove: Callable[[NotificationCard], None] | None = on_remove
        self._handlers: list[int] = []
        self._disposed = False
        self._image: Widget.Icon | None = None
        self._interactive_buttons: list[Widget.Button] = []
        self._click_controller: Gtk.GestureClick | None = None
        self._click_handler_ids: list[int] = []
        notification_assets.acquire(notification)

        icon = notification.icon or "application-x-executable-symbolic"
        self._image = _scaled_icon(
            icon,
            42 if popup else 40,
            ["notification-icon"],
            "application-x-executable-symbolic",
        )
        self._image.valign = "center"
        self._age_label = Widget.Label(
            label=_notification_age(notification.time),
            css_classes=["notification-age"],
            valign="center",
        )

        title = Widget.Label(
            label=notification.summary or notification.app_name,
            css_classes=["notification-title"],
            halign="start",
            hexpand=True,
            ellipsize="end",
            max_width_chars=34,
        )
        close_button = Widget.Button(
            child=Widget.Icon(image="window-close-symbolic", pixel_size=16),
            css_classes=["notification-close"],
            valign="start",
            on_click=lambda *_: self._dismiss(),
        )
        self._interactive_buttons.append(close_button)
        header = Widget.Box(
            spacing=7,
            valign="start",
            child=[title, self._age_label, close_button],
        )
        body = Widget.Label(
            label=notification.body,
            css_classes=["notification-body"],
            halign="start",
            justify="left",
            wrap=True,
            wrap_mode="word_char",
            max_width_chars=46,
            lines=2,
            ellipsize="end",
            visible=bool(notification.body),
        )

        text_children: list[Gtk.Widget] = [header, body]
        actions = self._action_buttons(notification)

        super().__init__(
            vertical=True,
            spacing=8,
            css_classes=[
                "notification-card",
                "notification-popup-card" if popup else "notification-history-card",
                f"notification-urgency-{notification.urgency}",
            ],
            child=[
                Widget.Box(
                    spacing=11,
                    child=[
                        self._image,
                        Widget.Box(
                            vertical=True,
                            spacing=3,
                            hexpand=True,
                            valign="start",
                            child=text_children,
                        ),
                    ],
                ),
                actions,
            ],
        )

        # Give the otherwise inert card a pressed state without claiming the
        # click or assigning it an action. Child action/dismiss buttons retain
        # their normal behavior.
        self._click_controller = Gtk.GestureClick()
        self._click_handler_ids.append(self._click_controller.connect(
            "pressed",
            lambda *_: self.set_state_flags(Gtk.StateFlags.ACTIVE, False),
        ))
        self._click_handler_ids.append(self._click_controller.connect(
            "released",
            lambda *_: self.unset_state_flags(Gtk.StateFlags.ACTIVE),
        ))
        self._click_handler_ids.append(self._click_controller.connect(
            "cancel",
            lambda *_: self.unset_state_flags(Gtk.StateFlags.ACTIVE),
        ))
        self.add_controller(self._click_controller)

        self._handlers.append(notification.connect("closed", self._on_closed))
        if popup:
            self._handlers.append(notification.connect("dismissed", self._on_dismissed))

    def _action_buttons(self, notification: Notification) -> Widget.Box | None:
        buttons: list[Gtk.Widget] = []
        for action in notification.actions:
            if action.id == "default":
                continue
            button = Widget.Button(
                    label=action.label,
                    css_classes=["notification-action"],
                    hexpand=True,
                    on_click=lambda _, selected=action: selected.invoke(),
                )
            buttons.append(button)
            self._interactive_buttons.append(button)
        if not buttons:
            return None
        return Widget.Box(
            homogeneous=True,
            spacing=6,
            css_classes=["notification-actions"],
            child=buttons,
        )

    def _refresh_age(self) -> None:
        notification = self._notification
        if notification is None:
            return
        self._age_label.label = _notification_age(notification.time)

    def _dismiss(self) -> None:
        notification = self._notification
        if notification is None:
            return
        if self._popup:
            notification.dismiss()
        else:
            notification.close()

    def _on_closed(self, *_args) -> None:
        self._remove()

    def _on_dismissed(self, *_args) -> None:
        self._remove()

    def _remove(self) -> None:
        callback = self._on_remove
        if callback is not None and not self._disposed:
            callback(self)

    def dispose_card(self) -> None:
        if self._disposed:
            return
        self._disposed = True

        notification = self._notification
        if notification is not None:
            for handler in self._handlers:
                if notification.handler_is_connected(handler):
                    notification.disconnect(handler)
        self._handlers.clear()

        for button in self._interactive_buttons:
            button.on_click = None
        self._interactive_buttons.clear()

        if self._click_controller is not None:
            for handler in self._click_handler_ids:
                if self._click_controller.handler_is_connected(handler):
                    self._click_controller.disconnect(handler)
            self.remove_controller(self._click_controller)
        self._click_handler_ids.clear()
        self._click_controller = None

        if self._image is not None:
            self._image.clear()
            self._image._image = None
        util.replace_box_children(self, [])
        self._image = None
        self._notification = None
        self._on_remove = None
        notification_assets.release(self._notification_id)


class MediaPlayer(Widget.Box):
    def __init__(self) -> None:
        self._player: MprisPlayer | None = None
        self._player_handlers: list[int] = []
        self._art: Widget.Icon | None = None
        super().__init__(
            vertical=True,
            css_classes=["notification-media-slot"],
            visible=False,
        )
        mpris_service.connect("notify::players", self._select_player)
        self._select_player()

    def _select_player(self, *_args) -> None:
        players = mpris_service.players
        player = next(
            (item for item in players if item.playback_status == "Playing"),
            players[0] if players else None,
        )
        if player is self._player:
            self._render()
            return

        self._disconnect_player()
        self._player = player
        if player is not None:
            for prop in (
                "art-url",
                "artist",
                "title",
                "playback-status",
                "can-go-next",
                "can-go-previous",
            ):
                self._player_handlers.append(player.connect(f"notify::{prop}", self._render))
        self._render()

    def _disconnect_player(self) -> None:
        if self._art is not None:
            self._art.clear()
            self._art._image = None
            self._art = None
        if self._player is not None:
            for handler in self._player_handlers:
                if self._player.handler_is_connected(handler):
                    self._player.disconnect(handler)
        self._player_handlers.clear()

    def _render(self, *_args) -> None:
        player = self._player
        if player is None:
            util.replace_box_children(self, [])
            self.visible = False
            return

        if self._art is not None:
            self._art.clear()
            self._art._image = None
        self._art = _scaled_icon(
            player.art_url,
            58,
            ["notification-media-art"],
            "audio-x-generic-symbolic",
        )
        art_frame = Widget.Box(
            css_classes=["notification-media-art-frame"],
            child=[self._art],
        )
        art_frame.set_overflow(Gtk.Overflow.HIDDEN)
        subtitle = player.artist or ""
        controls = Widget.Box(
            spacing=8,
            valign="center",
            css_classes=["notification-media-controls"],
            child=[
                Widget.Button(
                    child=Widget.Icon(image="media-skip-backward-symbolic", pixel_size=16),
                    sensitive=player.can_go_previous,
                    on_click=lambda *_: player.previous(),
                ),
                Widget.Button(
                    child=Widget.Icon(
                        image="media-playback-pause-symbolic"
                        if player.playback_status == "Playing"
                        else "media-playback-start-symbolic",
                        pixel_size=17,
                    ),
                    sensitive=player.can_pause or player.can_play,
                    on_click=lambda *_: player.play_pause(),
                ),
                Widget.Button(
                    child=Widget.Icon(image="media-skip-forward-symbolic", pixel_size=16),
                    sensitive=player.can_go_next,
                    on_click=lambda *_: player.next(),
                ),
            ],
        )
        util.replace_box_children(self, [
            Widget.Box(
                spacing=12,
                css_classes=["notification-media"],
                child=[
                    art_frame,
                    Widget.Box(
                        vertical=True,
                        spacing=3,
                        hexpand=True,
                        valign="center",
                        child=[
                            Widget.Label(
                                label=player.title or player.identity or "Unknown track",
                                css_classes=["notification-media-title"],
                                halign="start",
                                ellipsize="end",
                                max_width_chars=26,
                            ),
                            Widget.Label(
                                label=subtitle,
                                css_classes=["notification-media-subtitle"],
                                halign="start",
                                ellipsize="end",
                                max_width_chars=29,
                                visible=bool(subtitle),
                            ),
                        ],
                    ),
                    controls,
                ],
            )
        ])
        self.visible = True


class Notifications(Widget.Box):
    """GNOME-like notification history for the calendar overview."""

    def __init__(self) -> None:
        self._cards: dict[int, NotificationCard] = {}
        self._list = Widget.Box(
            vertical=True,
            spacing=9,
            css_classes=["notification-list"],
        )
        self._empty = Widget.Box(
            vertical=True,
            spacing=16,
            valign="center",
            halign="center",
            vexpand=True,
            can_target=False,
            css_classes=["notification-empty"],
            child=[
                Widget.Icon(image="notifications-symbolic", pixel_size=68),
                Widget.Label(label="No notifications"),
            ],
        )
        self._clear_button = Widget.Button(
            label="Clear all",
            css_classes=["notification-clear"],
            on_click=lambda *_: notification_service.clear_all(),
        )
        self._footer = Widget.Box(
            halign="end",
            valign="end",
            css_classes=["notification-footer"],
            child=[self._clear_button],
        )
        self._scroll_fade = Widget.Box(
            height_request=52,
            hexpand=True,
            valign="end",
            can_target=False,
            visible=False,
            css_classes=["notification-scroll-fade", "notification-scroll-fade-bottom"],
        )
        self._scroll_fade_top = Widget.Box(
            height_request=52,
            hexpand=True,
            valign="start",
            can_target=False,
            visible=False,
            css_classes=["notification-scroll-fade", "notification-scroll-fade-top"],
        )
        self._scroll = Widget.Scroll(
            vexpand=True,
            hscrollbar_policy="never",
            vscrollbar_policy="automatic",
            child=self._list,
        )
        adjustment = self._scroll.get_vadjustment()
        adjustment.connect("changed", self._sync_scroll_fade)
        adjustment.connect("value-changed", self._sync_scroll_fade)
        self._media = MediaPlayer()

        super().__init__(
            vertical=True,
            spacing=12,
            vexpand=True,
            css_classes=["nc-notifications"],
            child=[
                Widget.Overlay(
                    vexpand=True,
                    child=Widget.Box(
                        vertical=True,
                        spacing=12,
                        child=[
                            self._media,
                            Widget.Overlay(
                                vexpand=True,
                                child=self._scroll,
                                overlays=[
                                    self._scroll_fade_top,
                                    self._scroll_fade,
                                ],
                            ),
                            self._footer,
                        ],
                    ),
                    overlays=[
                        self._empty,
                    ],
                ),
            ],
        )

        for notification in reversed(notification_service.notifications):
            self._add(notification)
        notification_service.connect("notified", self._on_notified)
        self._media.connect("notify::visible", self._sync_empty_state)
        self._age_timeout = GLib.timeout_add_seconds(30, self._refresh_ages)
        self._sync_empty_state()

    def _refresh_ages(self) -> bool:
        for card in tuple(self._cards.values()):
            card._refresh_age()
        return GLib.SOURCE_CONTINUE

    def _on_notified(self, _service, notification: Notification) -> None:
        self._add(notification, newest=True)

    def _add(self, notification: Notification, newest: bool = False) -> None:
        if notification.id in self._cards:
            return
        card = NotificationCard(notification, popup=False, on_remove=self._remove)
        self._cards[notification.id] = card
        if newest:
            self._list.prepend(card)
        else:
            self._list.append(card)
        self._sync_empty_state()

    def _remove(self, card: NotificationCard) -> None:
        if self._cards.pop(card._notification_id, None) is None:
            return
        card.dispose_card()
        card.unparent()
        self._sync_empty_state()

    def _sync_empty_state(self, *_args) -> None:
        empty = not self._cards
        self._empty.visible = empty and not self._media.visible
        self._clear_button.sensitive = not empty

    def _sync_scroll_fade(self, adjustment, *_args) -> None:
        distance_from_top = max(0.0, adjustment.get_value())
        distance_from_bottom = max(
            0.0,
            adjustment.get_upper()
            - adjustment.get_page_size()
            - adjustment.get_value(),
        )
        top_opacity = min(1.0, distance_from_top / SCROLL_FADE_RAMP_PX)
        bottom_opacity = min(1.0, distance_from_bottom / SCROLL_FADE_RAMP_PX)

        has_cards = bool(self._cards)
        self._scroll_fade_top.opacity = top_opacity
        self._scroll_fade.opacity = bottom_opacity
        self._scroll_fade_top.visible = has_cards and top_opacity > 0
        self._scroll_fade.visible = has_cards and bottom_opacity > 0


class NotificationPopups(Widget.Window):
    """Animated popup stack, hosted by one window on the primary monitor."""

    def __init__(self) -> None:
        self._cards: dict[
            int,
            tuple[NotificationCard, Widget.Box, Widget.Revealer, Widget.Revealer],
        ] = {}
        self._closing: set[int] = set()
        self._suppressed: set[int] = set()
        self._list = Widget.Box(
            vertical=True,
            spacing=9,
            css_classes=["notification-popup-list"],
        )
        super().__init__(
            namespace="ignis_notification_popups",
            monitor=self._primary_monitor_id(),
            anchor=["top", "right"],
            layer="overlay",
            kb_mode="none",
            exclusivity="ignore",
            margin_top=42,
            margin_right=10,
            visible=False,
            css_classes=["window"],
            dynamic_input_region=True,
            child=Widget.Box(child=[self._list]),
        )
        notification_service.connect("new_popup", self._on_new_popup)

        # Imported lazily to avoid the Settings -> Bar -> this module cycle.
        from widgets.Settings import hyprland_settings

        hyprland_settings.connect("notify::primary-monitor", lambda *_: self._move_to_primary())
        for notification in notification_service.popups:
            self._add(notification)

    @staticmethod
    def _primary_monitor_id() -> int:
        from widgets.Settings import hyprland_settings

        for monitor in util.hyprland.monitors:
            if monitor.name == hyprland_settings.primary_monitor:
                return monitor.id
        return 0

    def _move_to_primary(self) -> None:
        self.monitor = self._primary_monitor_id()

    def _on_new_popup(self, _service, notification: Notification) -> None:
        self._add(notification)

    @staticmethod
    def _primary_monitor_has_fullscreen() -> bool:
        from widgets.Settings import hyprland_settings

        try:
            monitors = json.loads(util.hyprland.send_command("j/monitors"))
            clients = json.loads(util.hyprland.send_command("j/clients"))
        except (OSError, ValueError, TypeError):
            # If compositor state cannot be read, keep notifications visible.
            return False

        primary = next(
            (
                monitor
                for monitor in monitors
                if monitor.get("name") == hyprland_settings.primary_monitor
            ),
            None,
        )
        if primary is None:
            return False

        visible_workspaces = {
            workspace.get("id")
            for key in ("activeWorkspace", "specialWorkspace")
            if (workspace := primary.get(key)) and workspace.get("id") != 0
        }
        for client in clients:
            if client.get("monitor") != primary.get("id"):
                continue
            if not client.get("mapped", True) or client.get("hidden", False):
                continue

            visible = client.get("visible")
            if visible is None:
                visible = client.get("workspace", {}).get("id") in visible_workspaces
            if visible and client.get("fullscreen") in (2, 3):
                return True
        return False

    def _dismiss_suppressed(self, notification: Notification) -> bool:
        self._suppressed.discard(notification.id)
        notification.dismiss()
        return GLib.SOURCE_REMOVE

    def _add(self, notification: Notification) -> None:
        if notification.id in self._cards or notification.id in self._suppressed:
            return
        if self._primary_monitor_has_fullscreen():
            self._suppressed.add(notification.id)
            # new_popup is emitted before the service attaches its own
            # dismissed handler. Deferring ensures the popup is removed from
            # the service while the notification remains in history.
            GLib.idle_add(self._dismiss_suppressed, notification)
            return
        card = NotificationCard(notification, popup=True, on_remove=self._hide)
        inner = Widget.Revealer(
            transition_type="slide_left",
            transition_duration=POPUP_ANIMATION_MS,
            reveal_child=False,
            child=card,
        )
        outer = Widget.Revealer(
            transition_type="slide_down",
            transition_duration=POPUP_ANIMATION_MS,
            reveal_child=False,
            child=inner,
        )
        wrapper = Widget.Box(halign="end", child=[outer])
        self._cards[notification.id] = (card, wrapper, inner, outer)
        self._list.prepend(wrapper)
        self.visible = True
        outer.reveal_child = True
        GLib.timeout_add(POPUP_ANIMATION_MS, self._reveal, notification.id)

    def _reveal(self, notification_id: int) -> bool:
        item = self._cards.get(notification_id)
        if item is not None and notification_id not in self._closing:
            item[2].reveal_child = True
        return GLib.SOURCE_REMOVE

    def _hide(self, card: NotificationCard) -> None:
        item = self._cards.get(card._notification_id)
        if item is None or card._notification_id in self._closing:
            return
        self._closing.add(card._notification_id)
        item[2].transition_type = "crossfade"
        item[2].reveal_child = False
        GLib.timeout_add(
            POPUP_ANIMATION_MS,
            self._hide_outer,
            card._notification_id,
        )

    def _hide_outer(self, notification_id: int) -> bool:
        item = self._cards.get(notification_id)
        if item is not None:
            item[3].reveal_child = False
            GLib.timeout_add(POPUP_ANIMATION_MS, self._remove, notification_id)
        return GLib.SOURCE_REMOVE

    def _remove(self, notification_id: int) -> bool:
        item = self._cards.pop(notification_id, None)
        if item is None:
            return GLib.SOURCE_REMOVE
        card, wrapper, inner, outer = item
        card.dispose_card()
        inner.child = None
        outer.child = None
        wrapper.unparent()
        self._closing.discard(notification_id)
        if not self._cards:
            self.visible = False
        return GLib.SOURCE_REMOVE
