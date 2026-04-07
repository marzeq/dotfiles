from __future__ import annotations
import asyncio
import json
from gi.repository import Gio  # pyright: ignore[reportMissingModuleSource]
from ignis.services.applications import ApplicationsService, Application
from ignis.widgets import Widget
from util import JsonSettings
from .base_mode import LauncherMode, LauncherResult
import util

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
        refresh_apps()
        await asyncio.sleep(30)
        

asyncio.create_task(refresh_apps_loop())


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
        return app_name.lower() in self.hidden_apps

    @property
    def visible_apps(self) -> list[Application]:
        return [app for app in applications.apps if app.name.lower() not in self.read_hidden_apps()]


app_settings = AppSettings()


class AppMode(LauncherMode):
    async def get_results(self, launcher, query, emit):
        query = query.strip().lower()
        if not query:
            emit(
                [LauncherAppResult(app, launcher) for app in app_settings.visible_apps],
                True,
            )
            return

        emit(
            [LauncherAppResult(app, launcher) for app in app_settings.visible_apps],
            True,
        )


class LauncherAppResult(LauncherResult):
    def __init__(self, app: Application, launcher):
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
        self.launcher = launcher

    def launch_app(self):
        util.popup_manager.close_curr_popup()
        self.app.launch()

    def hide_app(self) -> None:
        app_settings.hide_app(self.app.name)
        self.launcher.update_mode_and_list(no_scroll_reset=True)
