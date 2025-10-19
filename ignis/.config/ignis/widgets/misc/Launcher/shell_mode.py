import subprocess
import util

from .base_mode import LauncherMode, LauncherResult

class ShellMode(LauncherMode):
    def matches(self, query: str) -> bool:
        return query.strip().startswith("$")

    def update(self, launcher, query: str):
        cmd = query.lstrip("$").strip()
        if not cmd:
            launcher.set_results([])
            return

        launcher.set_results([LauncherShellResult(cmd)])

    def launch(self, launcher):
        cmd = launcher.entry.text.lstrip("$").strip()
        if not cmd:
            return

        try:
            subprocess.Popen(["/usr/bin/env", "bash", "-c", cmd])
        except Exception:
            pass

        util.close_curr_popup()

class LauncherShellResult(LauncherResult):
    def __init__(self, cmd: str):
        super().__init__(
            label=cmd,
            icon_name="utilities-terminal-symbolic",
            launch=lambda: None,
            css_classes=["launcher-result-shell"],
        )
        self.cmd = cmd
