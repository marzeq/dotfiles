"""Small, shell-free subprocess helpers."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence


def run(
    command: Sequence[str],
    *,
    capture_output: bool = False,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command and turn failures into useful CLI errors."""
    try:
        return subprocess.run(
            command,
            check=True,
            capture_output=capture_output,
            input=input_text,
            text=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(f"Required command not found: {command[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "").strip()
        message = f"Command failed ({error.returncode}): {' '.join(command)}"
        raise RuntimeError(f"{message}\n{detail}" if detail else message) from error


def spawn(command: Sequence[str]) -> None:
    """Start a detached command without involving a shell."""
    try:
        subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(f"Required command not found: {command[0]}") from error
