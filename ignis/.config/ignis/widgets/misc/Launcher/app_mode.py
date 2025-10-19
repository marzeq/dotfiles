from ignis.services.applications import ApplicationsService, Application
from .base_mode import LauncherMode, LauncherResult
import util
from rapidfuzz import process, fuzz

applications = ApplicationsService.get_default()

class AppMode(LauncherMode):
    def matches(self, query: str) -> bool:
        return not query.startswith("=")

    def update(self, launcher, query: str):
        query = query.strip().lower()
        if not query:
            launcher.reset_entry()
            launcher.set_results([LauncherAppResult(app) for app in applications.apps])
            return

        apps = fuzzy_search(applications.apps, query)
        launcher.entry.css_classes = ["launcher-entry-input"]
        launcher.set_results([LauncherAppResult(app) for app in apps])

    def launch(self, launcher):
        launcher.trigger_result()

class LauncherAppResult(LauncherResult):
    def __init__(self, app: Application):
        super().__init__(
            label=app.name,
            icon_name=app.icon,
            icon_size="large",
            launch=lambda: self.launch_app(),
        )
        self.app = app

    def launch_app(self):
        util.close_curr_popup()
        self.app.launch()

def fuzzy_search(apps: list[Application], query: str) -> list[Application]:
    query = query.lower()
    if not query:
        return apps
    apps_by_name = {app.name.lower(): app for app in apps}
    matches = process.extract(
        query,
        apps_by_name.keys(),
        scorer=fuzz.WRatio,
        limit=10,
        score_cutoff=60,
    )
    return [apps_by_name[m[0]] for m in matches]
