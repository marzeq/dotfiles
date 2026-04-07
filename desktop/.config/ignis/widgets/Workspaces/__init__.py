from ignis.widgets import Widget
from ignis.services.hyprland import HyprlandService, HyprlandWorkspace

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
        super().__init__(
            child=[
                Widget.Button(
                    child=Widget.Box(
                        child=hyprland.bind_many(
                            ["workspaces", "active_workspace"],
                            transform=lambda workspaces,
                            *_: workspace_settings.bind_properties(
                                lambda *_: [
                                    Workspace(monitor_name, w) for w in workspaces
                                ]
                            ),
                        )
                    ),
                    css_classes=["box"],
                ),
            ],
            css_classes=["workspaces"],
        )
