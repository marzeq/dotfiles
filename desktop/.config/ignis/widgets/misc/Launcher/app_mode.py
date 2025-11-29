from __future__ import annotations
import json
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable
from ignis.gobject import IgnisGObject
from ignis.services.applications import ApplicationsService, Application
from ignis.widgets import Widget

if TYPE_CHECKING:
    from . import Launcher

from .base_mode import LauncherMode, LauncherResult
import util
from rapidfuzz import process, fuzz

SETTINGS_PATH = os.path.expanduser("~/.local/share/ignis/apps.json")
DECAY_HALF_LIFE_DAYS = 30

applications = ApplicationsService.get_default()

FrequencyEntry = dict[str, float]
Frequencies = dict[str, FrequencyEntry]

def decay_frequency(entry: FrequencyEntry) -> float:
    now = time.time()
    freq = entry.get("count", 0.0)
    last = entry.get("last_launch", 0.0)
    if freq <= 0 or last <= 0:
        return 0.0
    age_days = (now - last) / 86400
    return freq * (0.5 ** (age_days / DECAY_HALF_LIFE_DAYS))


@util.JsonSettings(SETTINGS_PATH)
class AppSettings(IgnisGObject):
    frequencies: Frequencies = {}
    hidden_apps: list[str] = []

    def hide_app(self, app_name: str) -> None:
        name = app_name.lower()
        if name not in self.hidden_apps:
            self.hidden_apps = self.hidden_apps + [name]

    def unhide_app(self, app_name: str) -> None:
        name = app_name.lower()
        self.hidden_apps = [x for x in self.hidden_apps if x != name]

    def record_launch(self, app_name: str) -> None:
        name = app_name.lower()
        entry = self.frequencies.get(
            name, {"count": 0.0, "last_launch": 0.0}
        )
        entry["count"] = float(entry.get("count", 0.0)) + 1.0
        entry["last_launch"] = time.time()

        freqs = dict(self.frequencies)
        freqs[name] = entry
        self.frequencies = freqs

    def decayed_frequency(self, app_name: str) -> float:
        entry = self.frequencies.get(app_name.lower())
        if not entry:
            return 0.0
        return decay_frequency(entry)

    def is_hidden(self, app_name: str) -> bool:
        return app_name.lower() in self.hidden_apps

    @property
    def visible_apps(self) -> list[Application]:
        hidden = set(self.hidden_apps)
        return [
            app for app in applications.apps
            if app.name.lower() not in hidden
        ]


app_settings = AppSettings()


class AppMode(LauncherMode):
    def matches(self, query: str) -> bool:
        return not query.startswith("=")

    def update(self, launcher, query: str):
        query = query.strip().lower()
        if not query:
            launcher.reset_entry()
            launcher.set_results([LauncherAppResult(app, launcher, self.update) for app in app_settings.visible_apps])
            return

        apps = fuzzy_search(app_settings.visible_apps, query)
        launcher.entry.css_classes = ["launcher-entry-input"]
        launcher.set_results([LauncherAppResult(app, launcher, self.update) for app in apps])

    def launch(self, launcher):
        launcher.trigger_result()


class LauncherAppResult(LauncherResult):
    def __init__(self, app: Application, launcher: Launcher, refresh_results: Callable[..., None]):
        self.refresh_results = refresh_results
        super().__init__(
            label=app.name,
            icon_name=app.icon,
            launch=lambda: self.launch_app(),
            popover_menu=Widget.PopoverMenu(
                items=[
                    Widget.MenuItem(
                        label="Hide",
                        on_activate=lambda _: self.hide_app()
                    )
                ]
            )
        )
        self.app = app
        self.launcher = launcher

    def launch_app(self):
        util.popup_manager.close_curr_popup()
        app_settings.record_launch(self.app.name)
        self.app.launch()

    def hide_app(self) -> None:
        app_settings.hide_app(self.app.name)
        self.refresh_results()

def fuzzy_search(apps: list[Application], query: str) -> list[Application]:
    query = query.lower()
    if not query:
        return apps

    apps_by_name = {app.name.lower(): app for app in apps}
    matches = process.extract(
        query,
        apps_by_name.keys(),
        scorer=fuzz.WRatio,
        limit=20,
        score_cutoff=60,
    )

    scored: list[tuple[str, float]] = []
    for name, score, _ in matches:
        freq_score = app_settings.decayed_frequency(name)
        boosted_score = score + min(freq_score * 3, 40)
        scored.append((name, boosted_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [apps_by_name[name] for name, _ in scored[:10]]
