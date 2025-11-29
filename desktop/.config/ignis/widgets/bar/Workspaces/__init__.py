from ignis.widgets import Widget
from ignis.services.hyprland import HyprlandService, HyprlandWorkspace

from util import JsonSettings, BindableSetting

hyprland = HyprlandService.get_default()
workspaces_first = 1
workspaces_last = 10

@JsonSettings("workspaces")
class WorkspaceSettings(BindableSetting):
    show_all_ws_on_monitor: bool = True
    def set_show_all_ws_on_monitor(self, value: bool) -> None: self.show_all_ws_on_monitor = value

    show_empty_workspaces: bool = False
    def set_show_empty_workspaces(self, value: bool) -> None: self.show_empty_workspaces = value

workspace_settings = WorkspaceSettings()

class Workspace(Widget.Box):
    def __init__(self, monitor_name: str, workspace: HyprlandWorkspace):
        if workspace.monitor != monitor_name and not workspace_settings.show_all_ws_on_monitor:
            super().__init__()
            return

        super().__init__(
            css_classes=["workspace"],
            halign="start",
            valign="center",
            child=[
            ]
        )
        if workspace.id == hyprland.active_workspace.id and workspace.monitor == monitor_name:
            self.add_css_class("active")
        if hyprland.get_monitor_by_name(monitor_name).active_workspace_id == workspace.id: # type: ignore
            self.add_css_class("visible")

class Workspaces(Widget.Box):
    def __init__(self, monitor_name: str):
        super().__init__(
            child=[
                Widget.Button(
                    child=Widget.Box(child=hyprland.bind_many(
                        ["workspaces", "active_workspace"],
                        transform=lambda workspaces, *_: workspace_settings.bind_properties(lambda *_: [
                            Workspace(monitor_name, i) for i in workspaces
                        ]),
                    )),
                    css_classes=["box"],
                ),
            ],
            css_classes=["workspaces"],
        )
