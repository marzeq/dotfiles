import subprocess
import os
from typing import Callable

from ignis.app import IgnisApp

app = IgnisApp.get_default()

def run_cmd(cmd: str) -> None:
    subprocess.Popen(
        ["/bin/bash", "-c", cmd],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setpgrp
    )

def run_cmd_and_run(cmd: str, runnable: Callable) -> None:
    runnable()
    run_cmd(cmd)
