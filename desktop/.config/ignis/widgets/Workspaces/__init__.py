import os

from gi.repository import Gio, GLib
from ignis.widgets import Widget

import util
from widgets.Settings import hyprland_settings


ACTIVE_WORKSPACE_PATH = os.path.expanduser(
    "~/.local/share/ignis/active-logical-workspace"
)


class Workspace(Widget.Box):
    def __init__(self, logical_id: int, active_id: int):
        classes = ["workspace"]
        if logical_id == active_id:
            classes.extend(["active", "visible"])
        super().__init__(
            css_classes=classes,
            halign="start",
            valign="center",
        )


class Workspaces(Widget.Box):
    def __init__(self, monitor_name: str):
        self._monitor_name = monitor_name
        self._tracked_windows: set[int] = set()
        monitor = util.hyprland.get_monitor_by_name(self._monitor_name)
        self._active_logical_id = (
            monitor.active_workspace_id if monitor is not None else 1
        )
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
        util.hyprland.connect("notify::workspaces", self._render)
        util.hyprland.connect("notify::windows", self._sync_window_signals)
        hyprland_settings.connect("notify::workspace-count", self._render)
        hyprland_settings.connect(
            "notify::workspaces-span-displays", self._render
        )
        hyprland_settings.connect("notify::hide-empty-workspaces", self._render)
        state_directory = Gio.File.new_for_path(
            os.path.dirname(ACTIVE_WORKSPACE_PATH)
        )
        self._state_monitor = state_directory.monitor_directory(
            Gio.FileMonitorFlags.NONE
        )
        self._state_monitor.connect("changed", self._state_changed)
        self._sync_window_signals()
        self._render()

    def _state_changed(
        self,
        _monitor,
        file: Gio.File,
        other_file: Gio.File | None,
        _event,
    ) -> None:
        changed_paths = {
            candidate.get_path()
            for candidate in (file, other_file)
            if candidate is not None
        }
        if ACTIVE_WORKSPACE_PATH in changed_paths:
            GLib.idle_add(self._read_active_workspace)

    def _read_active_workspace(self) -> bool:
        try:
            with open(ACTIVE_WORKSPACE_PATH, encoding="utf-8") as state_file:
                logical_id = int(state_file.read().strip())
        except (OSError, ValueError):
            return False
        if 1 <= logical_id <= hyprland_settings.workspace_count:
            self._active_logical_id = logical_id
            self._render()
        return False

    def _sync_window_signals(self, *_args) -> None:
        for window in util.hyprland.windows:
            identity = id(window)
            if identity not in self._tracked_windows:
                self._tracked_windows.add(identity)
                window.connect("notify::workspace-id", self._render)
                window.connect(
                    "closed",
                    lambda *_args, tracked=identity: (
                        self._tracked_windows.discard(tracked),
                        self._render(),
                    ),
                )
        self._render()

    def _physical_ids(self, logical_id: int) -> list[int]:
        monitors = sorted(util.hyprland.monitors, key=lambda monitor: monitor.id)
        primary = next(
            (
                monitor
                for monitor in monitors
                if monitor.name == hyprland_settings.primary_monitor
            ),
            monitors[0] if monitors else None,
        )
        if primary is None or not hyprland_settings.workspaces_span_displays:
            return [logical_id]

        ids = [logical_id]
        block = 1
        for monitor in monitors:
            if monitor.name != primary.name:
                ids.append(block * 10 + logical_id)
                block += 1
        return ids

    def _render(self, *_args) -> None:
        active_id = self._active_logical_id
        occupied_ids = {
            window.workspace_id for window in util.hyprland.windows
        }

        def visible(logical_id: int) -> bool:
            if not hyprland_settings.hide_empty_workspaces:
                return True
            if logical_id == active_id:
                return True
            return any(
                physical_id in occupied_ids
                for physical_id in self._physical_ids(logical_id)
            )

        util.replace_box_children(
            self._workspace_box,
            [
                Workspace(logical_id, active_id)
                for logical_id in range(1, hyprland_settings.workspace_count + 1)
                if visible(logical_id)
            ],
        )
