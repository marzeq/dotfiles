from datetime import datetime
import os
from typing import Any, Callable
import gi
from ignis.services.upower import UPowerService
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
from widgets.FilteredPicture import FilteredPicture
from widgets.Settings.style_settings import style_settings
from widgets.Settings import hyprland_settings
from widgets.Tray import tray_settings


upower = UPowerService.get_default()


lock_windows = []


def lock():
    # NOTE: Due to a regression in gtk4-layer-shell's gtk_session_lock_instance_unlock() on GTK4 4.22.2+,
    # calling self._lock_instance.unlock() on line 361 causes a segmentation fault.
    # This is a regression in the native library, not a Python code issue.
    # As such, LockScreen functionality is currently disabled. The lockscreen will not appear and we instead will trigger a system suspend as a fallback
    util.sync_shell("loginctl lock-session")
    return
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
        self._time_label = Widget.Label(
            label="",
            css_classes=["lockscreen-time"],
        )
        self._date_label = Widget.Label(
            label="",
            css_classes=["lockscreen-date"],
        )
        self._time_date_task: asyncio.Task[None] | None = None

        super().__init__(
            vertical=True,
            hexpand=False,
            halign="center",
            valign="center",
            child=[
                self._time_label,
                self._date_label,
            ],
        )
        self.connect("realize", self._start_updates)
        self.connect("unrealize", self._stop_updates)

    def _start_updates(self, *_args) -> None:
        if self._time_date_task is None or self._time_date_task.done():
            self._time_date_task = util.create_task(self._update_time_date_loop())

    def _stop_updates(self, *_args) -> None:
        if self._time_date_task is not None:
            self._time_date_task.cancel()
            self._time_date_task = None

    async def _update_time_date_loop(self):
        try:
            while True:
                self._time_label.set_label(
                    datetime.now().strftime(
                        clock_settings.hour_format(
                            show_seconds=False,
                            show_am_pm=True,
                        )
                    )
                )
                self._date_label.set_label(
                    datetime.now().strftime(
                        clock_settings.date_format(long=True, show_dow=True)
                    )
                )
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            return

    def destroy(self):
        self._stop_updates()


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

    def set_authenticating(self, authenticating: bool):
        self.entry.set_editable(not authenticating)
        self.entry.set_visibility(False)

        if authenticating:
            self.entry.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, "content-loading-symbolic"
            )
            self.entry.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, False)
        else:
            self.entry.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, "view-conceal-symbolic"
            )
            self.entry.set_icon_activatable(Gtk.EntryIconPosition.SECONDARY, True)


class LockScreen(Widget.Window):
    def __init__(self, lock_instance, monitor: Gdk.Display, monitor_id: int):
        super().__init__(
            visible=False, layer="top", namespace=f"ignis_lockscreen_{monitor_id}"
        )

        self._destroyed = False
        self._upower_batteries_handler_id: int | None = None
        self._battery = None
        self._battery_handler_ids: list[int] = []
        self._tray_settings_handler_id: int | None = None

        lock_instance.assign_window_to_monitor(self, monitor)

        self._wallpaper = FilteredPicture(
            image=style_settings.wallpaper,
            blur_radius=16,
            darken=0.5,
            content_fit="cover",
        )

        if (
            hyprland_settings.primary_monitor
            != [m for m in util.hyprland.monitors if m.id == monitor_id][0].name
        ):
            self.set_child(self._wallpaper)
            return

        self.authenticating = False
        self._lock_instance = lock_instance

        self.time_revealer = Widget.Revealer(
            child=TimeDateScreen(),
            transition_type="slide_down",
            transition_duration=util.popup_manager.popup_anim_speed * 2,
            reveal_child=True,
        )

        self.entry_screen = EntryScreen(
            on_accept=lambda t: None
            if self.authenticating
            else util.create_task(self._on_accept(t)),
            on_change=lambda: self._on_change(),
        )
        self.entry = self.entry_screen.entry
        self.entry_revealer = Widget.Revealer(
            child=self.entry_screen,
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

        self.battery_status = Widget.Box(
            css_classes=["battery-status"],
        ) 

        self.set_child(
            Widget.Overlay(
                child=Widget.EventBox(
                    child=[self._wallpaper],
                    on_click=lambda *_: self.show_entry(),
                    on_right_click=lambda *_: self.show_entry(),
                    on_middle_click=lambda *_: self.show_entry(),
                ),
                overlays=[
                    Widget.Box(
                        child=[self.battery_status],
                        vexpand=True,
                        hexpand=True,
                        valign="start",
                        halign="end",
                    ),
                    content
                ],
            )
        )

        key_controller = Gtk.EventControllerKey()
        self.add_controller(key_controller)
        key_controller.connect(
            "key-pressed", lambda *x: self._handle_keypress(x[1] == 65307, x[1])
        )

        def on_batteries_changed(*_):
            self.update_battery_status()

        self._upower_batteries_handler_id = upower.connect(
            "notify::batteries", on_batteries_changed
        )
        self._tray_settings_handler_id = tray_settings.connect(
            "notify::show-batt-percent", self._refresh_battery_status
        )
        self.update_battery_status()

    def destroy(self):
        if self._destroyed:
            return

        self._destroyed = True

        handler_id = self._upower_batteries_handler_id
        if handler_id is not None:
            disconnect = getattr(upower, "disconnect", None)
            if callable(disconnect):
                try:
                    disconnect(handler_id)
                except Exception:
                    pass
            self._upower_batteries_handler_id = None

        if self._tray_settings_handler_id is not None:
            tray_settings.disconnect(self._tray_settings_handler_id)
            self._tray_settings_handler_id = None
        self._disconnect_battery()

        self._wallpaper.set_property("image", "")
        self.set_child(None)
        super().destroy()

    def show_entry(self):
        if not self.entry_revealer.get_reveal_child():
            self.entry_revealer.set_reveal_child(True)
            self.time_revealer.set_reveal_child(False)
            self.entry.grab_focus()

    def _handle_keypress(self, is_esc: bool, keycode: int):
        if self.authenticating:
            return

        if self.entry_revealer.get_reveal_child() and is_esc:
            self.entry_revealer.set_reveal_child(False)
            self.time_revealer.set_reveal_child(True)
            self.entry.set_text("")
        elif self.time_revealer.get_reveal_child():
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

    def set_authenticating(self, authenticating: bool):
        self.authenticating = authenticating
        self.entry_screen.set_authenticating(authenticating)

    async def _on_accept(self, text: str):
        self.set_authenticating(True)

        if not await async_auth(getpass.getuser(), text.strip()):
            self.set_authenticating(False)
            self.entry.add_css_class("error")
            return

        self.set_authenticating(False)
        self.entry.remove_css_class("error")

        self._lock_instance.unlock()
        destroy_windows()

    def update_battery_status(self):
        self._disconnect_battery()
        if len(upower.batteries) == 0:
            self.battery_status.visible = False
            util.replace_box_children(self.battery_status, [])
            return

        self._battery = upower.display_device
        batt = self._battery

        self.battery_status.visible = True
        self._battery_icon = Widget.Icon()
        self._battery_label = Widget.Label()
        util.replace_box_children(
            self.battery_status, [self._battery_icon, self._battery_label]
        )
        for prop in ("icon-name", "charging", "percent"):
            self._battery_handler_ids.append(
                batt.connect(f"notify::{prop}", self._refresh_battery_status)
            )
        self._refresh_battery_status()

    def _disconnect_battery(self) -> None:
        if self._battery is not None:
            for handler in self._battery_handler_ids:
                if self._battery.handler_is_connected(handler):
                    self._battery.disconnect(handler)
        self._battery_handler_ids.clear()
        self._battery = None

    def _refresh_battery_status(self, *_args) -> None:
        batt = self._battery
        if batt is None:
            return
        self._battery_icon.image = batt.icon_name
        self._battery_icon.css_classes = ["battery-charging"] if batt.charging else []
        show_percent = tray_settings.show_batt_percent
        self._battery_label.label = f"{int(batt.percent)}%" if show_percent else ""
        self._battery_label.css_classes = ["batt-percent"] if show_percent else []


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
