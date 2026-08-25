from ignis.widgets import Widget
from ignis.services.hyprland import HyprlandService, HyprlandWorkspace

import util
from util import JsonSettings, BindableSettings

hyprland = HyprlandService.get_default()


@JsonSettings("workspaces")
class WorkspaceSettings(BindableSettings):
    show_all_ws_on_monitor: bool = True

    def set_show_all_ws_on_monitor(self, value: bool):
        self.show_all_ws_on_monitor = value


workspace_settings = WorkspaceSettings()


class Workspace(Widget.Box):
    def __init__(self, monitor_name: str, workspace: HyprlandWorkspace):
        super().__init__(
            css_classes=["workspace"],
            halign="start",
            valign="center",
            visible=workspace.monitor == monitor_name
            or workspace_settings.show_all_ws_on_monitor,
        )

        if (
            workspace.id == hyprland.active_workspace.id
            and workspace.monitor == monitor_name
        ):
            self.add_css_class("active")
        
        monitor = hyprland.get_monitor_by_name(monitor_name)
        if monitor is not None and monitor.active_workspace_id == workspace.id:
            self.add_css_class("visible")


class Workspaces(Widget.Box):
    def __init__(self, monitor_name: str):
        self._monitor_name = monitor_name
        self._workspace_box = Widget.Box()
        super().__init__(
            child=[
                Widget.Button(
                    child=self._workspace_box,
                    css_classes=["box"],
                ),
            ],
            css_classes=["workspaces"],
        )
        hyprland.connect("notify::workspaces", self._render)
        hyprland.connect("notify::active-workspace", self._render)
        workspace_settings.connect("notify::show-all-ws-on-monitor", self._render)
        self._render()

    def _render(self, *_args) -> None:
        util.replace_box_children(
            self._workspace_box,
            [Workspace(self._monitor_name, workspace) for workspace in hyprland.workspaces],
        )
