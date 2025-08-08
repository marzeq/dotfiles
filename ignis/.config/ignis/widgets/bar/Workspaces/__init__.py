from ignis.widgets import Widget
from ignis.services.hyprland import HyprlandService, HyprlandWorkspace

hyprland = HyprlandService.get_default()
workspaces_first = 1
workspaces_last = 10

def Workspaces(monitor_name: str) -> Widget.EventBox:
    def WorkspaceButton(workspace: HyprlandWorkspace) -> Widget.Button:
        widget = Widget.Box(
            css_classes=["workspace"],
            halign="start",
            valign="center",
        )
        if workspace.id == hyprland.active_workspace.id and workspace.monitor == monitor_name:
            widget.add_css_class("active")
        if hyprland.get_monitor_by_name(monitor_name).active_workspace_id == workspace.id: # type: ignore
            widget.add_css_class("visible")

        return widget

    return Widget.Box(
        child=[
            Widget.Box(
                child=hyprland.bind_many(
                    ["workspaces", "active_workspace"],
                    transform=lambda workspaces, *_: [
                        WorkspaceButton(i) for i in workspaces
                    ],
                ),
                css_classes=["box"],
            ),
        ],
        css_classes=["workspaces"],
    )
