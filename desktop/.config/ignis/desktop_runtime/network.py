"""Network actions not provided directly by the Ignis service."""

from __future__ import annotations

from .process import run


def toggle_ethernet() -> None:
    result = run(
        ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device"],
        capture_output=True,
    )
    for line in result.stdout.splitlines():
        device, separator, remainder = line.partition(":")
        device_type, second_separator, state = remainder.partition(":")
        if separator and second_separator and device_type == "ethernet":
            action = "disconnect" if state == "connected" else "connect"
            run(["nmcli", "device", action, device])
            return
    raise RuntimeError("No Ethernet device found")
