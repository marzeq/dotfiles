from datetime import datetime
import gi
import pam
import getpass

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4SessionLock", "1.0")

from ignis.widgets import Widget
from ignis.utils import Utils
from gi.repository import Gtk4SessionLock
from widgets.bar.Clock import clock_settings

lock_windows = []

def lock():
    lock_instance = Gtk4SessionLock.Instance.new()
    lock_instance.lock()
    for i, m in enumerate(Utils.get_monitors()): # type: ignore
        window = LockScreen(lock_instance, i)
        lock_instance.assign_window_to_monitor(window, m)
        lock_windows.append(window)

def destroy_windows():
    for window in lock_windows:
        window.destroy()

class LockScreen(Widget.Window):
    def __init__(self, lock_instance, monitor_id: int):
        self._lock_instance = lock_instance
        self.entry = Widget.Entry(
            style="",
            on_accept=self._on_accept,
            hexpand=False,
        )
        self.entry.set_visibility(False)
        super().__init__(
            visible=False,
            layer="top",
            namespace=f"lockcreen-window-{monitor_id}",
            child=Widget.CenterBox(
                vertical=True,
                hexpand=False,
                center_widget=Widget.Box(
                    vertical=True,
                    child=[
                        Widget.Label(
                            label=clock_settings.bind_properties(
                                lambda *_: Utils.Poll(1000, lambda _:
                                    datetime.now().strftime(
                                        clock_settings.hour_format(
                                            show_seconds=False
                                        )
                                    )).bind("output")
                            )
                        ),
                        Widget.Label(
                            label=clock_settings.bind_properties(
                                lambda *_: Utils.Poll(1000, lambda _:
                                    datetime.now().strftime(
                                        clock_settings.date_format(long=True, show_dow=True)
                                    )).bind("output")
                            )
                        ),
                        self.entry
                    ] if monitor_id == 0 else []
                )
            )
        )

    def _on_accept(self, _):
        if not pam.authenticate(getpass.getuser(), (self.entry.get_text() or "").strip()):
            return
        self._lock_instance.unlock()
        destroy_windows()

# TODO: make systemd aware of our custom lockscreen, chatgpt generated something like this, needs validation tho
# import os
# import signal
# import sys
#
# import gi
# gi.require_version("Gtk", "4.0")
# gi.require_version("Gtk4SessionLock", "1.0")
#
# from ignis.widgets import Widget
# from ignis.utils import Utils
# from gi.repository import Gtk4SessionLock as SessionLock
# from gi.repository import GLib, Gio
#
# lock_windows = []
# lock_instance = None
#
# def lock():
#     global lock_instance
#     if lock_instance is None:
#         lock_instance = SessionLock.Instance.new()
#     lock_instance.lock()
#     for monitor in Utils.get_monitors():
#         window = LockScreen(lock_instance, monitor)
#         SessionLock.Instance.assign_window_to_monitor(lock_instance, window, monitor)
#         window.present()
#         lock_windows.append(window)
#
# def destroy_windows():
#     global lock_windows, lock_instance
#     for window in lock_windows:
#         window.destroy()
#     lock_windows = []
#     lock_instance = None
#
# class LockScreen(Widget.Window):
#     def __init__(self, lock_inst, monitor):
#         self._lock_instance = lock_inst
#         super().__init__(
#             visible=False,
#             layer="top",
#             namespace=f"lockscreen-window-{monitor.get_connector()}",
#         )
#         self.entry = Widget.Entry(
#             style="border: 2px solid red;",
#             on_accept=self._on_accept,
#         )
#         self.entry.set_visibility(False)
#         self.child = self.entry
#
#     def _on_accept(self, _):
#         # replace with your PAM code
#         from pam import pam
#         import getpass
#         if not pam().authenticate(getpass.getuser(),
#                                  (self.entry.get_text() or "").strip()):
#             return
#         self._lock_instance.unlock()
#         destroy_windows()
#
# def on_login1_signal(connection, sender_name, object_path, interface, signal, params):
#     if signal == "Lock":
#         lock()
#     elif signal == "Unlock":
#         destroy_windows()
#
# def main():
#     session_id = os.getenv("XDG_SESSION_ID")
#     if session_id is None:
#         print("XDG_SESSION_ID not set; cannot watch loginctl signals.", file=sys.stderr)
#         sys.exit(1)
#
#     bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
#
#     lm = bus.get_proxy("org.freedesktop.login1",
#                        "/org/freedesktop/login1",
#                        "org.freedesktop.login1.Manager")
#
#     try:
#         session_path = lm.call_sync("GetSession", GLib.Variant("(s)", (session_id,)),
#                                     Gio.DBusCallFlags.NONE, -1, None).unpack()[0]
#     except Exception as e:
#         print("Could not get session path:", e, file=sys.stderr)
#         sys.exit(1)
#
#     bus.call_sync(
#         None,
#         "org.freedesktop.login1",
#         session_path,
#         "org.freedesktop.DBus.Properties",
#         "Get",
#         GLib.Variant("(ss)", ("org.freedesktop.login1.Session", "Id")),
#         Gio.DBusCallFlags.NONE,
#         -1,
#         None,
#     )  # just to check is valid
#
#     bus.signal_subscribe(
#         sender="org.freedesktop.login1",
#         object_path=session_path,
#         interface_name="org.freedesktop.login1.Session",
#         signal_name="Lock",
#         arg0=None,
#         flags=Gio.DBusSignalFlags.NONE,
#         callback=on_login1_signal,
#     )
#     bus.signal_subscribe(
#         sender="org.freedesktop.login1",
#         object_path=session_path,
#         interface_name="org.freedesktop.login1.Session",
#         signal_name="Unlock",
#         arg0=None,
#         flags=Gio.DBusSignalFlags.NONE,
#         callback=on_login1_signal,
#     )
#
#     # optional: also catch when loginctl lock-session is called via Manager
#     bus.signal_subscribe(
#         sender="org.freedesktop.login1",
#         object_path="/org/freedesktop/login1",
#         interface_name="org.freedesktop.login1.Manager",
#         signal_name="LockSessions",
#         arg0=None,
#         flags=Gio.DBusSignalFlags.NONE,
#         callback=lambda *args: lock(),
#     )
#
#     loop = GLib.MainLoop()
#     for s in (signal.SIGINT, signal.SIGTERM):
#         signal.signal(s, lambda *_: loop.quit())
#     loop.run()
#
# if __name__ == "__main__":
#     main()
#
