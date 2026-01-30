from typing import Literal

import util
from .base_mode import LauncherMode, LauncherResult

Action = Literal[
    "shutdown",
    "shutdown_alt",
    "reboot",
    "logout",
    "suspend",
    "sleep",
]

actions: list[Action] = [
    "shutdown",
    "shutdown_alt",
    "reboot",
    "logout",
    "suspend",
    "sleep",
]


def Action_repr(action: Action) -> str:
    match action:
        case "shutdown":
            return "Power Off"
        case "shutdown_alt":
            return "Shutdown"
        case "reboot":
            return "Reboot"
        case "logout":
            return "Log Out"
        case "suspend":
            return "Suspend"
        case "sleep":
            return "Sleep"


class PowerOffMode(LauncherMode):
    async def get_results(self, launcher, query, emit):
        if query.strip() == "":
            emit([], True)
            return

        emit(
            [LauncherPowerOffResult(action) for action in actions],
            True,
        )


class LauncherPowerOffResult(LauncherResult):
    def __init__(self, action: Action):
        self.action: Action = action
        super().__init__(
            value=Action_repr(action),
            icon_name=self.icon_name(),
            launch=lambda: self.launch(),
            css_classes=["launcher-result-value"],
        )

    def launch(self):
        util.popup_manager.close_curr_popup()

        if self.action in ("shutdown", "shutdown_alt"):
            util.shell("systemctl poweroff")
        elif self.action == "reboot":
            util.shell("systemctl reboot")
        elif self.action == "logout":
            util.shell("hyprctl dispatch exit")
        elif self.action in ("suspend", "sleep"):
            util.shell("systemctl suspend")

    def icon_name(self) -> str:
        icons: dict[Action, str] = {
            "shutdown": "system-shutdown-symbolic",
            "shutdown_alt": "system-shutdown-symbolic",
            "reboot": "system-reboot-symbolic",
            "logout": "system-log-out-symbolic",
            "suspend": "weather-clear-night-symbolic",
            "sleep": "weather-clear-night-symbolic",
        }
        return icons[self.action]
