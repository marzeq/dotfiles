from ignis.widgets import Widget
from ignis.services.applications import ApplicationsService, Application

from gi.repository import Gtk  # type: ignore

import utils

applications = ApplicationsService.get_default()

def LauncherApp(app: Application):
    def launch():
        nonlocal app
        utils.close_curr_popup()
        app.launch()

    return Widget.Button(
        css_classes=["launcher-app"],
        child=Widget.Box(
            child=([
                Widget.Icon(image=app.icon, css_classes=["launcher-app-icon"], pixel_size=32),
            ] if app.icon else []) + ([
                Widget.Label(label=app.name),
            ])
        ),
        on_click=lambda *_: launch(),
    )

def Launcher(monitor: int):
    entry = Widget.Entry(
        hexpand=True,
        placeholder_text="Search",
        css_classes=["launcher-entry-input"],
    )

    app_list = Widget.Box(
        vertical=True,
        css_classes=["launcher-app-list"],
        child = [
            LauncherApp(app) for app in applications.apps
        ]
    )

    window = Widget.Window(
        visible=False,
        popup=True,
        kb_mode="on_demand",
        monitor=monitor,
        layer="top",
        anchor=["top", "right", "bottom", "left"],
        namespace=f"ignis_launcher_{monitor}",
        css_classes=["window"],
        child=Widget.Overlay(
            child=Widget.EventBox(
                vexpand=True,
                hexpand=True,
                on_click=lambda _: utils.close_curr_popup(),
            ),
            overlays=[
                Widget.Box(
                    vertical=True,
                    valign="center",
                    halign="center",
                    css_classes=["launcher"],
                    child=[
                        Widget.Box(
                            css_classes=["launcher-entry"],
                            child=[
                                Widget.Icon(
                                    icon_name="system-search-symbolic",
                                    css_classes=["launcher-entry-icon"],
                                ),
                                entry
                            ],
                        ),
                        Widget.Scroll(
                            child=app_list,
                            vexpand=True,
                        ),
                    ],
                ),
            ],
        ),
    )

    def reset_entry():
        nonlocal entry
        entry.text = ""
        entry.grab_focus()
        entry.css_classes = ["launcher-entry-input", "launcher-entry-empty"]

    def update_app_list():
        nonlocal app_list, entry
        query = entry.text.strip().lower()

        if query == "":
            entry.grab_focus()
            reset_entry()
            app_list.child = [ # type: ignore
                LauncherApp(app) for app in applications.apps
            ]
            return
        
        entry.css_classes = ["launcher-entry-input"]
        
        apps = applications.search(applications.apps, query)
        if not apps:
            app_list.child = [] # type: ignore
            return

        app_list.child = [ # type: ignore
            LauncherApp(app) for app in apps
        ]

    def launch():
        nonlocal entry, app_list
        if not app_list.visible:
            return

        app_list.child[0].on_click() # type: ignore

    entry.on_change = lambda *_: update_app_list() # type: ignore
    entry.on_accept = lambda *_: launch() # type: ignore

    key_controller = Gtk.EventControllerKey()
    window.add_controller(key_controller)
    key_controller.connect("key-pressed", lambda *x: utils.clear_popupers() or utils.reset_popup() if x[1] == 65307 else None)  # 65307 = ESC
    window.connect("notify::visible", lambda *_: reset_entry() if window.visible else None)

    return window

def LauncherProxy():
    window = Widget.Window(
        namespace="ignis_launcher_proxy",
        layer="background",
        css_classes=["window"],
        visible=False,
    )

    def close_window():
        nonlocal window
        window.visible = False

    window.connect("notify::visible", lambda *_: utils.handle_popup_clicked("ignis_launcher") or close_window() if window.visible else None)

    return window
