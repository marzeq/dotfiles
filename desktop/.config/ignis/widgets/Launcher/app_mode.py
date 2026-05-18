from __future__ import annotations
import json
from ignis.services.applications import ApplicationsService, Application
from ignis.widgets import Widget
from util import JsonSettings
from .base_mode import LauncherMode, LauncherResult, fuzzy_search_results
import util

applications = ApplicationsService.get_default()


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
        return [app for app in applications.apps if app.name.lower() not in self.read_hidden_apps()]


app_settings = AppSettings()


class AppMode(LauncherMode):
    def build(self, launcher):
        super().build(launcher)
        self.all_results = [LauncherAppResult(app, self) for app in app_settings.visible_apps]
        self.set_results(self.all_results)
        self.section.visible = bool(self.results)
        return self.section

    async def update(self, query: str, refresh):
        query = query.strip().lower()

        if not self.results:
            self.section.visible = False
            refresh()
            return

        if not query:
            self.results = list(self.all_results)
            self.section.set_child(self.results)

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
        self.section.set_child(self.results)
        self.section.visible = bool(self.visible_results())
        refresh()


class LauncherAppResult(LauncherResult):
    def __init__(self, app: Application, mode: AppMode):
        super().__init__(
            value=app.name,
            icon_name=app.icon,
            launch=lambda: self.launch_app(),
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
