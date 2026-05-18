from __future__ import annotations
from ignis.services.applications.application import Application
from ignis.services.applications.service import ApplicationsService
from ignis.widgets import Widget
from gi.repository import Gio, Gtk, Gdk  # pyright: ignore[reportMissingModuleSource]
import util
import asyncio
from widgets.Launcher.base_mode import LauncherResult
from rapidfuzz import fuzz

from .app_mode import AppMode
from .calc_mode import CalcMode
from .base_mode import LauncherMode
from .poweroff_mode import PowerOffMode
from .currency_mode import CurrencyMode


class Launcher(Widget.RevealerWindow):
    def __init__(self, monitorid: int, monitor: Gdk.Monitor):
        self._search_task: asyncio.Task | None = None
        self._search_gen = 0

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

        self.modes: list[LauncherMode] = [
            AppMode(),
            CalcMode(),
            PowerOffMode(),
            CurrencyMode(),
        ]

        self._build_result_tree()

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
            self._on_visible_changed,
        )

        applications = ApplicationsService.get_default()


        def refresh_apps():
            applications._apps = {}

            for app in Gio.AppInfo.get_all():
                if isinstance(app, Gio.DesktopAppInfo):
                    if app.get_nodisplay():
                        continue

                    obj = Application(app=app)

                    applications._apps[obj.id] = obj

            applications.notify("apps")
            applications.notify("pinned")


        async def refresh_apps_loop():
            while True:
                await asyncio.sleep(30)
                refresh_apps()
                self._build_result_tree()
                

        asyncio.create_task(refresh_apps_loop())

        self.update_mode_and_list()

    def _build_result_tree(self):
        sections = [mode.build(self) for mode in self.modes]
        self.result_list.set_child(sections)
        self.refresh_results_layout()

    def _cancel_search_task(self):
        if self._search_task and not self._search_task.done():
            self._search_task.cancel()
        self._search_task = None

    def _on_visible_changed(self, *_):
        if self.visible:
            self.reset_entry()
        else:
            self._cancel_search_task()

    def refresh_results_layout(self):
        visible_results = self.get_results()
        if len(visible_results) <= 4:
            self.scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
            self.scroller.css_classes = []
        else:
            self.scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            self.scroller.css_classes = ["launcher-scroller-scrolling"]

    def set_entry_text(self, text: str):
        self.entry.text = text
        self.entry.grab_focus_without_selecting()
        self.entry.set_position(len(text))
        self.update_mode_and_list()

    def reset_entry(self):
        self.entry.text = ""
        self.entry.grab_focus()
        self.entry.css_classes = ["launcher-entry-input", "launcher-entry-empty"]
        self.update_mode_and_list()

    def update_mode_and_list(self, no_scroll_reset: bool = False):
        query = self.entry.text.strip()

        if query == "":
            self.entry.css_classes = ["launcher-entry-input", "launcher-entry-empty"]
        else:
            self.entry.css_classes = ["launcher-entry-input"]

        self._search_gen += 1
        gen = self._search_gen

        self._cancel_search_task()

        if not no_scroll_reset:
            self.reset_scroll_state()

        async def delayed():
            try:
                await asyncio.sleep(0.05)
                if gen == self._search_gen:
                    await self._run_search(query)
            except asyncio.CancelledError:
                return
            finally:
                if self._search_task is asyncio.current_task():
                    self._search_task = None

        self._search_task = asyncio.create_task(delayed())

    async def _run_search(self, query: str):
        await asyncio.gather(*(mode.update(query, self.refresh_results_layout) for mode in self.modes))
        self._reorganize_results_by_quality(query)
        self.refresh_results_layout()

    def _reorganize_results_by_quality(self, query: str):
        """Reorganize mode sections by best match quality in query"""
        if not query.strip():
            # If no query, keep original mode order
            return

        mode_scores = []
        for mode in self.modes:
            visible_results = mode.visible_results()
            if visible_results:
                # Get highest fuzzy match score for this mode's results
                best_score = max(
                    fuzz.WRatio(query.lower(), result.value.lower())
                    for result in visible_results
                )
                mode_scores.append((best_score, mode))

        # Sort modes by best match score (descending)
        mode_scores.sort(key=lambda x: x[0], reverse=True)

        # Reorder sections in result_list based on match quality
        new_sections = [score_mode[1].section for score_mode in mode_scores]
        # Add any modes without visible results at the end
        for mode in self.modes:
            if not any(mode == score_mode[1] for score_mode in mode_scores):
                new_sections.append(mode.section)

        self.result_list.set_child(new_sections)

    def get_results(self) -> list[LauncherResult]:
        return [result for mode in self.modes for result in mode.visible_results()]

    def reset_scroll_state(self):
        self.scroller.get_vadjustment().set_value(0)

    def trigger_result(self, index: int = 0):
        results = self.get_results()
        if results and index < len(results):
            results[index].on_click()


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
