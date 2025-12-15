from __future__ import annotations
from ignis.services.applications import ApplicationsService, Application
from ignis.widgets import Widget
from util import JsonSettings
from .base_mode import GetResultsResponse, LauncherMode, LauncherResult
import util

applications = ApplicationsService.get_default()


@JsonSettings("apps")
class AppSettings:
    hidden_apps: list[str] = []

    def hide_app(self, app_name: str) -> None:
        name = app_name.lower()
        if name not in self.hidden_apps:
            self.hidden_apps = self.hidden_apps + [name]

    def unhide_app(self, app_name: str) -> None:
        name = app_name.lower()
        self.hidden_apps = [x for x in self.hidden_apps if x != name]

    def is_hidden(self, app_name: str) -> bool:
        return app_name.lower() in self.hidden_apps

    @property
    def visible_apps(self) -> list[Application]:
        hidden = set(self.hidden_apps)
        return [app for app in applications.apps if app.name.lower() not in hidden]


app_settings = AppSettings()


class AppMode(LauncherMode):
    def matches(self, query: str) -> bool:
        return not query.startswith("=")

    def get_results(self, launcher, query: str):
        query = query.strip().lower()
        if not query:
            return GetResultsResponse(
                [LauncherAppResult(app) for app in app_settings.visible_apps]
            )

        return GetResultsResponse(
            [LauncherAppResult(app) for app in app_settings.visible_apps]
        )


class LauncherAppResult(LauncherResult):
    def __init__(self, app: Application):
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

    def launch_app(self):
        util.popup_manager.close_curr_popup()
        self.app.launch()

    def hide_app(self) -> None:
        app_settings.hide_app(self.app.name)
