from datetime import datetime
import os
from typing import Any, Callable
import gi
import pam
import getpass
import unicodedata
import asyncio
import util

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4SessionLock", "1.0")

from ignis.widgets import Widget
from ignis.utils import Utils
from gi.repository import Gtk, Gdk, Gio, Gtk4SessionLock  # type: ignore
from widgets.Clock import clock_settings
from widgets.BlurredPicture import BlurredPicture
from widgets.Settings.style_manager import StyleManager

sm = StyleManager.instance()

lock_windows = []


def lock():
    global lock_windows
    lock_instance = Gtk4SessionLock.Instance.new()
    lock_instance.lock()
    for i, m in enumerate(Utils.get_monitors()):  # type: ignore
        window = LockScreen(lock_instance, m, i)
        lock_windows.append(window)


def destroy_windows():
    global lock_windows
    for window in lock_windows:
        window.destroy()
    lock_windows = []


def sync_auth(user: str, password: str) -> bool:
    try:
        return pam.authenticate(user, password)
    except:
        return False


async def async_auth(user: str, password: str) -> bool:
    return await asyncio.to_thread(sync_auth, user, password)


class TimeDateScreen(Widget.Box):
    def __init__(self):
        super().__init__(
            vertical=True,
            hexpand=False,
            halign="center",
            valign="center",
            child=[
                Widget.Label(
                    label=clock_settings.bind_properties(
                        lambda *_: Utils.Poll(
                            1000,
                            lambda _: datetime.now().strftime(
                                clock_settings.hour_format(show_seconds=False)
                            ),
                        ).bind("output")
                    ),
                    css_classes=["lockscreen-time"],
                ),
                Widget.Label(
                    label=clock_settings.bind_properties(
                        lambda *_: Utils.Poll(
                            1000,
                            lambda _: datetime.now().strftime(
                                clock_settings.date_format(long=True, show_dow=True)
                            ),
                        ).bind("output")
                    ),
                    css_classes=["lockscreen-date"],
                ),
            ],
        )


class EntryScreen(Widget.Box):
    def __init__(self, on_accept: Callable[[str], Any], on_change: Callable[[], Any]):
        self.entry = Widget.Entry(
            on_change=lambda _: on_change(),
            on_accept=lambda _: on_accept(self.entry.get_text() or ""),
            hexpand=False,
            valign="center",
            css_classes=["lockscreen-entry"],
        )
        self.entry.set_visibility(False)
        self.entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, "view-conceal-symbolic"
        )
        self.entry.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, True)
        self.entry.connect("icon-press", self._on_icon_press)
        self.entry.connect("icon-release", self._on_icon_release)

        pic = get_user_profile_picture()

        pfp_frame = Gtk.Frame()
        pfp_frame.get_style_context().add_class("lockscreen-usericon-frame")
        pfp_frame.set_child(
            Widget.Icon(
                hexpand=False,
                valign="center",
                halign="center",
                image=pic if pic else "avatar-default-symbolic",
                css_classes=["lockscreen-usericon-default"] if not pic else [],
                pixel_size=192 if pic else 128,
            )
        )

        super().__init__(
            vertical=True,
            hexpand=False,
            halign="center",
            valign="center",
            child=[
                Widget.Box(
                    halign="center",
                    valign="center",
                    hexpand=False,
                    vexpand=False,
                    child=[pfp_frame],
                    css_classes=["lockscreen-usericon-bg"],
                ),
                Widget.Label(
                    label=getpass.getuser(), css_classes=["lockscreen-username"]
                ),
                self.entry,
            ],
        )

    def _on_icon_press(self, entry, position):
        if position != Gtk.EntryIconPosition.SECONDARY:
            return
        entry.set_visibility(True)
        entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, "view-reveal-symbolic"
        )

    def _on_icon_release(self, entry, position):
        if position != Gtk.EntryIconPosition.SECONDARY:
            return
        entry.set_visibility(False)
        entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, "view-conceal-symbolic"
        )


class LockScreen(Widget.Window):
    def __init__(self, lock_instance, monitor: Gdk.Display, monitor_id: int):
        super().__init__(
            visible=False, layer="top", namespace=f"ignis_lockscreen_{monitor_id}"
        )

        lock_instance.assign_window_to_monitor(self, monitor)

        wallpaper = BlurredPicture(
            image=sm.wallpaper_symlink, blur_radius=16, content_fit="cover"
        )

        if monitor_id != 0:
            self.set_child(wallpaper)
            return

        self.authenticating = False
        self._lock_instance = lock_instance

        self.time_revealer = Widget.Revealer(
            child=TimeDateScreen(),
            transition_type="slide_down",
            transition_duration=util.popup_manager.popup_anim_speed * 2,
            reveal_child=True,
        )

        entry_screen = EntryScreen(
            on_accept=lambda t: None
            if self.authenticating
            else asyncio.create_task(self._on_accept(t)),
            on_change=lambda: self._on_change(),
        )
        self.entry = entry_screen.entry
        self.entry_revealer = Widget.Revealer(
            child=entry_screen,
            transition_type="slide_up",
            transition_duration=util.popup_manager.popup_anim_speed * 2,
            reveal_child=False,
        )

        content = Widget.Box(
            vertical=True,
            hexpand=False,
            vexpand=True,
            halign="center",
            valign="center",
            child=[self.time_revealer, self.entry_revealer],
        )

        content.style = "margin-bottom: 100px;"

        self.set_child(Widget.Overlay(child=wallpaper, overlays=[content]))

        key_controller = Gtk.EventControllerKey()
        self.add_controller(key_controller)
        key_controller.connect(
            "key-pressed", lambda *x: self._handle_keypress(x[1] == 65307, x[1])
        )

    def _handle_keypress(self, is_esc: bool, keycode: int):
        if self.authenticating:
            return

        if self.entry_revealer.get_reveal_child() and is_esc:
            self.entry_revealer.set_reveal_child(False)
            self.time_revealer.set_reveal_child(True)

            self.entry.set_text("")
        elif self.time_revealer.get_reveal_child() and not is_esc:
            self.time_revealer.set_reveal_child(False)
            self.entry_revealer.set_reveal_child(True)

            self.entry.grab_focus()
            if is_keycode_valid_in_pwd(keycode):
                char = chr(Gdk.keyval_to_unicode(keycode))
                current_text = self.entry.get_text() or ""
                self.entry.set_text(current_text + char)
                self.entry.set_position(-1)

    def _on_change(self):
        self.entry.remove_css_class("error")

    async def _on_accept(self, text: str):
        self.authenticating = True
        self.entry.set_editable(False)

        if not await async_auth(getpass.getuser(), text.strip()):
            self.authenticating = False
            self.entry.add_css_class("error")
            self.entry.set_editable(True)
            return

        self.autenticating = False
        self.entry.remove_css_class("error")
        self.entry.set_editable(True)

        self._lock_instance.unlock()
        destroy_windows()


class LockProxy(Widget.Window):
    def __init__(self):
        super().__init__(
            namespace="ignis_lock_proxy",
            layer="background",
            css_classes=["window"],
            visible=False,
        )

        self.connect(
            "notify::visible",
            lambda *_: lock() or self.close() if self.visible else None,
        )

    def close(self):
        self.visible = False


def is_keycode_valid_in_pwd(keyval: int) -> bool:
    ch = Gdk.keyval_to_unicode(keyval)
    if ch == 0:
        return False

    c = chr(ch)

    if unicodedata.category(c)[0] == "C":
        return False

    if c in ("\n", "\r", "\t"):
        return False

    return True


def get_user_profile_picture() -> str:
    uid = os.getuid()
    obj_path = f"/org/freedesktop/Accounts/User{uid}"

    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)

    proxy = Gio.DBusProxy.new_sync(
        bus,
        Gio.DBusProxyFlags.NONE,
        None,
        "org.freedesktop.Accounts",
        obj_path,
        "org.freedesktop.Accounts.User",
        None,
    )

    prop = proxy.get_cached_property("IconFile")

    if not prop:
        return ""

    s = prop.get_string()

    if os.path.isfile(s):
        return s

    return ""
