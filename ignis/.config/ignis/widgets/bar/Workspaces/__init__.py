from ignis.widgets import Widget
from ignis.services.hyprland import HyprlandService, HyprlandWorkspace

hyprland = HyprlandService.get_default()
workspaces_first = 1
workspaces_last = 10

class WorkspaceButton(Widget.Box):
    def __init__(self, monitor_name: str, workspace: HyprlandWorkspace):
        super().__init__(
            css_classes=["workspace"],
            halign="start",
            valign="center",
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
                        transform=lambda workspaces, *_: [
                            WorkspaceButton(monitor_name, i) for i in workspaces
                        ],
                    )),
                    css_classes=["box"],
                ),
            ],
            css_classes=["workspaces"],
        )
