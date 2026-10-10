"""XDG autostart launcher."""

from pathlib import Path

from .process import spawn


def launch_xdg_autostart() -> None:
    autostart_dir = Path.home() / ".config" / "autostart"
    for desktop_file in sorted(autostart_dir.glob("*.desktop")):
        spawn(["gio", "launch", str(desktop_file)])
