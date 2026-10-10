"""Session-level process actions."""

import subprocess

from .process import spawn


def restart_hypridle() -> None:
    try:
        subprocess.run(
            ["pkill", "-x", "hypridle"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as error:
        raise RuntimeError("Required command not found: pkill") from error
    spawn(["hypridle"])
