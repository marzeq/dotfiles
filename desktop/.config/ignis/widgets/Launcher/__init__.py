from __future__ import annotations
from typing import Sequence
from ignis.widgets import Widget
from gi.repository import Gtk, Gdk
from rapidfuzz import fuzz, process
import util
from widgets.Launcher.base_mode import LauncherResult

from .app_mode import AppMode
from .calc_mode import CalcMode
from .base_mode import LauncherMode


class Launcher(Widget.RevealerWindow):
    def __init__(self, monitorid: int, monitor: Gdk.Monitor):
        self.entry = Widget.Entry(
            hexpand=True,
            placeholder_text="Search",
            css_classes=["launcher-entry-input"],
        )

        self.result_list = Widget.Box(
            vertical=True, css_classes=["launcher-result-list"], child=[]
        )

        self.scroller = Widget.Scroll(
            child=self.result_list,
            css_classes=[],
        )

        monitor_geo = monitor.get_geometry()
        monitor_h_px: int = monitor_geo.height

        revealer = Widget.Revealer(
            transition_type="slide_down",
            child=Widget.Box(
                vertical=True,
                child=[
                    Widget.EventBox(
                        vexpand=True,
                        hexpand=True,
                        style=f"min-height: {monitor_h_px / 3}px;",
                        on_click=lambda _: util.popup_manager.close_curr_popup(),
                    ),
                    Widget.Box(
                        vertical=True,
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
                            self.scroller,
                        ],
                    ),
                ],
            ),
            transition_duration=util.popup_manager.popup_anim_speed,
            reveal_child=True,
        )

        super().__init__(
            visible=False,
            popup=True,
            kb_mode="on_demand",
            monitor=monitorid,
            layer="top",
            anchor=["top", "right", "bottom", "left"],
            namespace=f"ignis_launcher_{monitorid}",
            css_classes=["window"],
            child=Widget.Overlay(
                child=Widget.EventBox(
                    vexpand=True,
                    hexpand=True,
                    on_click=lambda _: util.popup_manager.close_curr_popup(),
                ),
                overlays=[
                    Widget.Box(
                        valign="start",
                        halign="center",
                        vertical=True,
                        child=[
                            revealer,
                        ],
                    )
                ],
            ),
            revealer=revealer,
        )

        self.modes: list[LauncherMode] = [AppMode(), CalcMode()]

        self.entry.on_change = lambda *_: self.update_mode_and_list()
        self.entry.on_accept = lambda *_: self.trigger_result(0)

        key_controller = Gtk.EventControllerKey()
        self.add_controller(key_controller)
        key_controller.connect(
            "key-pressed",
            lambda *x: util.popup_manager.clear_popupers()
            or util.popup_manager.reset_popup()
            if x[1] == 65307
            else None,
        )

        self.connect(
            "notify::visible",
            lambda *_: self.reset_scroll_state()
            or (self.reset_entry() if self.visible else None),
        )

        self.update_mode_and_list()

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

        results = []
        results_no_fuzz = []

        for mode in self.modes:
            got = mode.get_results(self, query)
            if got.include_in_fuzzing:
                results.extend(got.results)
            else:
                results_no_fuzz.extend(got.results)

        searched_results = results_no_fuzz + fuzzy_search(results, query)

        self.set_results(searched_results)

    def get_results(self) -> list[LauncherResult]:
        return self.result_list.child

    def reset_scroll_state(self):
        self.scroller.get_vadjustment().set_value(0)

    def set_results(self, results: Sequence[LauncherResult]):
        self.result_list.child = results
        if len(results) <= 4:
            self.scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
            self.scroller.css_classes = []
        else:
            self.scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            self.scroller.css_classes = ["launcher-scroller-scrolling"]

        self.reset_scroll_state()

    def trigger_result(self, index: int = 0):
        if self.result_list.child and index < len(self.result_list.child):
            self.result_list.child[index].on_click()


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
            lambda *_: util.popup_manager.handle_popup_clicked("ignis_launcher")
            or self.close()
            if self.visible
            else None,
        )

    def close(self):
        self.visible = False


def fuzzy_search(results: list[LauncherResult], query: str) -> list[LauncherResult]:
    query = query.lower()
    if not query:
        return results

    apps_by_name = {result.value.lower(): result for result in results}
    matches = process.extract(
        query,
        apps_by_name.keys(),
        scorer=fuzz.WRatio,
        limit=20,
        score_cutoff=60,
    )

    return [apps_by_name[match[0]] for match in matches]
