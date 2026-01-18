from typing import Literal

import util
from .base_mode import GetResultsResponse, LauncherMode, LauncherResult

Action = Literal["shutdown", "reboot", "logout", "suspend"]
actions: list[Action] = ["shutdown", "reboot", "logout", "suspend"]


def Action_repr(action: Action) -> str:
    match action:
        case "shutdown":
            return "Power Off"
        case "reboot":
            return "Reboot"
        case "logout":
            return "Log Out"
        case "suspend":
            return "Suspend"


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
        if self.action == "shutdown":
            util.shell("systemctl poweroff")
        elif self.action == "reboot":
            util.shell("systemctl reboot")
        elif self.action == "logout":
            util.shell("hyprctl dispatch exit")
        elif self.action == "suspend":
            util.shell("systemctl suspend")

    def icon_name(self) -> str:
        icons: dict[Action, str] = {
            "shutdown": "system-shutdown-symbolic",
            "reboot": "system-reboot-symbolic",
            "logout": "system-log-out-symbolic",
            "suspend": "weather-clear-night-symbolic",
        }
        return icons.get(self.action, "system-shutdown-symbolic")
