from __future__ import annotations
from ignis.widgets import Widget
from gi.repository import Gtk # type: ignore
import util

from .app_mode import AppMode, LauncherAppResult, applications
from .calc_mode import CalcMode
from .shell_mode import ShellMode
from .files_mode import FilesMode

class Launcher(Widget.Window):
    def __init__(self, monitor: int):
        self.entry = Widget.Entry(
            hexpand=True,
            placeholder_text="Search",
            css_classes=["launcher-entry-input"],
        )

        self.result_list = Widget.Box(
            vertical=True,
            css_classes=["launcher-result-list"],
            child=[LauncherAppResult(app) for app in applications.apps],
        )

        super().__init__(
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
                    on_click=lambda _: util.close_curr_popup(),
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
                                    self.entry,
                                ],
                            ),
                            Widget.Scroll(
                                child=self.result_list,
                                vexpand=True,
                            ),
                        ],
                    ),
                ],
            ),
        )

        self.modes = [CalcMode(), ShellMode(), FilesMode(), AppMode()]
        self.active_mode = self.modes[-1]

        self.entry.on_change = lambda *_: self.update_mode_and_list() # type: ignore
        self.entry.on_accept = lambda *_: self.active_mode.launch(self) # type: ignore

        key_controller = Gtk.EventControllerKey()
        self.add_controller(key_controller)
        key_controller.connect(
            "key-pressed",
            lambda *x: util.clear_popupers() or util.reset_popup()
            if x[1] == 65307
            else None,
        )

        self.connect(
            "notify::visible",
            lambda *_: self.reset_entry() if self.visible else None,
        )

    def set_entry_text(self, text: str):
        self.entry.text = text
        self.entry.grab_focus_without_selecting()
        self.entry.set_position(len(text))
        self.update_mode_and_list()

    def reset_entry(self):
        self.entry.text = ""
        self.entry.grab_focus()
        self.entry.css_classes = ["launcher-entry-input", "launcher-entry-empty"]

    def update_mode_and_list(self):
        query = self.entry.text.strip()

        if query == "":
            self.entry.css_classes = ["launcher-entry-input", "launcher-entry-empty"]
        else:
            self.entry.css_classes = ["launcher-entry-input"]

        for mode in self.modes:
            if mode.matches(query):
                self.active_mode = mode
                mode.update(self, query)
                return

class LauncherProxy(Widget.Window):
    def __init__(self):
        super().__init__(
            namespace="ignis_launcher_proxy",
            layer="background",
            css_classes=["window"],
            visible=False,
        )

        self.connect(
            "notify::visible",
            lambda *_: util.handle_popup_clicked("ignis_launcher") or self.close()
            if self.visible
            else None,
        )

    def close(self):
        self.visible = False
