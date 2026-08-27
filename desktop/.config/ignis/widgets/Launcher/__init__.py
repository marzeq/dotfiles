from __future__ import annotations
from ignis.widgets import Widget
from gi.repository import Gtk, Gdk  # pyright: ignore[reportMissingModuleSource]
import util
import asyncio
from widgets.Launcher.base_mode import LauncherResult
from rapidfuzz import fuzz

from .app_mode import AppMode
from .calc_mode import CalcMode
from .base_mode import LauncherMode
from .poweroff_mode import PowerOffMode
from .currency_mode import CurrencyMode
from .settings import launcher_settings


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
        self._displayed_modes: list[LauncherMode] = self._enabled_modes()

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

        self.update_mode_and_list()

    def _refresh_app_mode(self) -> None:
        for mode in self.modes:
            if isinstance(mode, AppMode):
                mode.refresh_apps()
                break

    def _build_result_tree(self):
        for mode in self.modes:
            mode.build(self)
        self._sync_enabled_mode_sections()
        self.refresh_results_layout()

    def _mode_enabled(self, mode: LauncherMode) -> bool:
        if isinstance(mode, AppMode):
            return True
        if isinstance(mode, CalcMode):
            return launcher_settings.calculator_enabled
        if isinstance(mode, CurrencyMode):
            return launcher_settings.currency_enabled
        if isinstance(mode, PowerOffMode):
            return launcher_settings.power_actions_enabled
        return True

    def _enabled_modes(self) -> list[LauncherMode]:
        return [mode for mode in self.modes if self._mode_enabled(mode)]

    def _sync_enabled_mode_sections(self) -> None:
        enabled_modes = self._enabled_modes()
        for mode in self.modes:
            if mode not in enabled_modes:
                mode.section.visible = False
        self._displayed_modes = enabled_modes
        util.replace_box_children(
            self.result_list, [mode.section for mode in enabled_modes]
        )

    def _cancel_search_task(self):
        if self._search_task and not self._search_task.done():
            self._search_task.cancel()
        self._search_task = None

    def _on_visible_changed(self, *_):
        if self.visible:
            self._refresh_app_mode()
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

        self._sync_enabled_mode_sections()

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

        self._search_task = util.create_task(delayed())

    async def _run_search(self, query: str):
        enabled_modes = self._enabled_modes()
        await asyncio.gather(
            *(
                mode.update(query, self.refresh_results_layout)
                for mode in enabled_modes
            )
        )
        self._reorganize_results_by_quality(query)
        self.refresh_results_layout()

    def _reorganize_results_by_quality(self, query: str):
        """Reorganize mode sections by best match quality in query"""
        enabled_modes = self._enabled_modes()
        if not query.strip():
            self._displayed_modes = enabled_modes
            util.replace_box_children(
                self.result_list, [mode.section for mode in self._displayed_modes]
            )
            return

        mode_scores = []
        for mode in enabled_modes:
            visible_results = mode.visible_results()
            if visible_results:
                best_score = max(
                    fuzz.WRatio(query.lower(), result.value.lower())
                    for result in visible_results
                )
                mode_scores.append((best_score, mode))

        # A valid calculation should always be the first visible result (and
        # therefore the result activated by Enter). Other modes retain their
        # fuzzy-match ordering beneath it.
        mode_scores.sort(
            key=lambda scored: (
                isinstance(scored[1], CalcMode),
                scored[0],
            ),
            reverse=True,
        )

        new_modes = [score_mode[1] for score_mode in mode_scores]
        for mode in enabled_modes:
            if mode not in new_modes:
                new_modes.append(mode)

        self._displayed_modes = new_modes
        util.replace_box_children(
            self.result_list, [mode.section for mode in self._displayed_modes]
        )

    def get_results(self) -> list[LauncherResult]:
        return [result for mode in self._displayed_modes for result in mode.visible_results()]

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
