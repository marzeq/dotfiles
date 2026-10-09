from __future__ import annotations
import json
import os
from pathlib import Path
from ignis.services.applications import ApplicationsService, Application
from ignis.widgets import Widget
from gi.repository import Gio  # pyright: ignore[reportMissingModuleSource]
from util import JsonSettings
from .base_mode import LauncherMode, LauncherResult, fuzzy_search_results
import util

applications = ApplicationsService.get_default()


def _flatpak_export_dirs() -> tuple[Path, ...]:
    data_home = Path(
        os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share"
    )
    return (
        data_home / "flatpak/exports/share/applications",
        Path("/var/lib/flatpak/exports/share/applications"),
    )


def _available_apps() -> list[Application]:
    """Return Gio apps plus Flatpak exports missing from Ignis' cached list."""
    apps_by_id = {app.id: app for app in applications.apps}

    # Ignis populates its service through Gio.AppInfo.get_all().  Gio determines
    # its search path from the environment present when the shell starts, so a
    # shell launched without Flatpak's XDG_DATA_DIRS entries never sees exported
    # desktop files.  Load the two standard export locations explicitly as a
    # fallback; opening the launcher also makes newly installed apps appear.
    for export_dir in _flatpak_export_dirs():
        try:
            desktop_files = list(export_dir.glob("*.desktop"))
        except OSError:
            continue

        for desktop_file in desktop_files:
            app_info = Gio.DesktopAppInfo.new_from_filename(str(desktop_file))
            if app_info is None or app_info.get_nodisplay():
                continue

            app = Application(app=app_info)
            if app.id is not None:
                apps_by_id.setdefault(app.id, app)

    return sorted(apps_by_id.values(), key=lambda app: app.name)


@JsonSettings("apps")
class AppSettings:
    hidden_apps: str = ""

    def read_hidden_apps(self) -> list[str]:
        return json.loads(self.hidden_apps) if self.hidden_apps else []

    def save_hidden_apps(self, apps: list[str]) -> None:
        self.hidden_apps = json.dumps(apps)

    def hide_app(self, app_name: str) -> None:
        name = app_name.lower()
        hidden = self.read_hidden_apps()
        if name not in hidden:
            hidden.append(name)
            self.save_hidden_apps(hidden)

    def unhide_app(self, app_name: str) -> None:
        name = app_name.lower()
        hidden = self.read_hidden_apps()
        if name in hidden:
            hidden.remove(name)
            self.save_hidden_apps(hidden)

    def is_hidden(self, app_name: str) -> bool:
        return app_name.lower() in self.read_hidden_apps()

    @property
    def visible_apps(self) -> list[Application]:
        hidden_apps = self.read_hidden_apps()
        return [app for app in _available_apps() if app.name.lower() not in hidden_apps]


app_settings = AppSettings()


class AppMode(LauncherMode):
    def build(self, launcher):
        super().build(launcher)
        self._results_by_id: dict[str, LauncherAppResult] = {}
        self.all_results: list[LauncherAppResult] = []
        self.refresh_apps()
        return self.section

    def refresh_apps(self) -> None:
        refreshed_results: list[LauncherAppResult] = []
        refreshed_by_id: dict[str, LauncherAppResult] = {}

        for app in app_settings.visible_apps:
            app_id = app.id
            result = self._results_by_id.get(app_id)
            if result is None:
                result = LauncherAppResult(app, self)
            else:
                result.app = app
                if result.value != app.name:
                    result.set_value(app.name)
                result.set_search_terms(self._app_search_terms(app))

            refreshed_results.append(result)
            refreshed_by_id[app_id] = result

        self._results_by_id = refreshed_by_id
        self.all_results = refreshed_results
        self.set_results(self.all_results)
        self.section.visible = bool(self.results)

    @staticmethod
    def _app_search_terms(app: Application) -> list[str]:
        app_id = app.id.removesuffix(".desktop") if app.id else None
        return (
            ([app.description] if app.description else [])
            + app.keywords
            + ([app_id] if app_id else [])
        )

    async def update(self, query: str, refresh):
        query = query.strip().lower()

        if not self.results:
            self.section.visible = False
            refresh()
            return

        if not query:
            self.results = list(self.all_results)
            util.replace_box_children(self.section, self.results)

            for result in self.results:
                result.visible = not app_settings.is_hidden(result.value)
            self.section.visible = bool(self.visible_results())
            refresh()
            return

        matched_results = fuzzy_search_results(self.all_results, query)
        matched_names = {result.value.lower() for result in matched_results}

        ordered_results = matched_results + [
            result for result in self.all_results if result.value.lower() not in matched_names
        ]

        for result in self.results:
            result.visible = (
                result.value.lower() in matched_names
                and not app_settings.is_hidden(result.value)
            )

        self.results = ordered_results
        util.replace_box_children(self.section, self.results)
        self.section.visible = bool(self.visible_results())
        refresh()


class LauncherAppResult(LauncherResult):
    def __init__(self, app: Application, mode: AppMode):
        super().__init__(
            value=app.name,
            icon_name=app.icon,
            launch=lambda: self.launch_app(),
            search_terms=mode._app_search_terms(app),
            popover_menu=Widget.PopoverMenu(
                items=[
                    Widget.MenuItem(label="Hide", on_activate=lambda _: self.hide_app())
                ]
            ),
        )
        self.app = app
        self.mode = mode

    def launch_app(self):
        util.popup_manager.close_curr_popup()
        self.app.launch()

    def hide_app(self) -> None:
        app_settings.hide_app(self.app.name)
        if self.mode.launcher is not None:
            self.mode.launcher.update_mode_and_list(no_scroll_reset=True)
