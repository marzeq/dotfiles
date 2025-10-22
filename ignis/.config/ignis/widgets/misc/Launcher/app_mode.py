from __future__ import annotations
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING
from ignis.services.applications import ApplicationsService, Application
from ignis.widgets import Widget

if TYPE_CHECKING:
    from . import Launcher

from .base_mode import LauncherMode, LauncherResult
import util
from rapidfuzz import process, fuzz

DATA_PATH = Path.home() / ".local/share/ignis"
FREQ_FILE = DATA_PATH / "app_freq.json"
HIDDEN_FILE = DATA_PATH / "hidden_apps.json"
DECAY_HALF_LIFE_DAYS = 30

applications = ApplicationsService.get_default()

FrequencyEntry = dict[str, float]
Frequencies = dict[str, FrequencyEntry]


def load_frequencies() -> Frequencies:
    if not FREQ_FILE.exists():
        return {}
    with open(FREQ_FILE, "r") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {}
    freqs: Frequencies = {}
    for k, v in data.items():
        if isinstance(v, dict):
            freqs[k] = {
                "count": float(v.get("count", 0)),
                "last_launch": float(v.get("last_launch", 0)),
            }
    return freqs


def save_frequencies(freqs: Frequencies):
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    with open(FREQ_FILE, "w") as f:
        json.dump(freqs, f)


def decay_frequency(freq_entry: FrequencyEntry) -> float:
    now = time.time()
    freq = freq_entry.get("count", 0)
    last = freq_entry.get("last_launch", 0)
    if freq <= 0 or last == 0:
        return 0
    age_days = (now - last) / 86400
    decay_factor = 0.5 ** (age_days / DECAY_HALF_LIFE_DAYS)
    return freq * decay_factor


def load_hidden_apps() -> list[str]:
    if not HIDDEN_FILE.exists():
        return []
    with open(HIDDEN_FILE, "r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []
    return [str(x).lower() for x in data]


def save_hidden_apps(hidden: list[str]):
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    with open(HIDDEN_FILE, "w") as f:
        json.dump(hidden, f)

FREQUENCIES: Frequencies = load_frequencies()
HIDDEN_APPS: list[str] = load_hidden_apps()


def hide_app(app_name: str):
    """Add app to hidden apps and reload HIDDEN_APPS."""
    global HIDDEN_APPS
    hidden = load_hidden_apps()
    name = app_name.lower()
    if name not in hidden:
        hidden.append(name)
        save_hidden_apps(hidden)
        HIDDEN_APPS = hidden

def record_launch(app_name: str):
    """Increment launch count and reload FREQUENCIES."""
    global FREQUENCIES
    name = app_name.lower()
    entry = FREQUENCIES.get(name, {"count": 0.0, "last_launch": 0.0})
    entry["count"] = entry.get("count", 0.0) + 1.0
    entry["last_launch"] = time.time()
    FREQUENCIES[name] = entry
    save_frequencies(FREQUENCIES)


def get_visible_apps() -> list[Application]:
    """Return all apps that are not hidden."""
    return [app for app in applications.apps if app.name.lower() not in HIDDEN_APPS]


class AppMode(LauncherMode):
    def matches(self, query: str) -> bool:
        return not query.startswith("=")

    def update(self, launcher, query: str):
        query = query.strip().lower()
        visible_apps = get_visible_apps()
        if not query:
            launcher.reset_entry()
            launcher.set_results([LauncherAppResult(app, launcher) for app in visible_apps])
            return

        apps = fuzzy_search(visible_apps, query)
        launcher.entry.css_classes = ["launcher-entry-input"]
        launcher.set_results([LauncherAppResult(app, launcher) for app in apps])

    def launch(self, launcher):
        launcher.trigger_result()


class LauncherAppResult(LauncherResult):
    def __init__(self, app: Application, launcher: Launcher):
        super().__init__(
            label=app.name,
            icon_name=app.icon,
            launch=lambda: self.launch_app(),
            popover_menu=Widget.PopoverMenu(
                items=[
                    Widget.MenuItem(
                        label="Hide",
                        on_activate=lambda _: hide_app(app.name)
                    )
                ]
            )
        )
        self.app = app
        self.launcher = launcher

    def launch_app(self):
        util.close_curr_popup()
        record_launch(self.app.name)
        self.app.launch()

    def hide_app(self):
        hide_app(self.app.name)
        self.launcher.update_mode_and_list()


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
        freq_score = decay_frequency(FREQUENCIES.get(name, {}))
        boosted_score = score + min(freq_score * 3, 40)
        scored.append((name, boosted_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [apps_by_name[name] for name, _ in scored[:10]]
