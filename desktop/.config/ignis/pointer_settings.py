"""Logical pointer-speed mapping for Hyprland/libinput.

The speed exposed by libinput is profile-dependent.  In particular, the flat
profile uses ``1 + speed`` as its constant gain, while the adaptive mouse
profile keeps ordinary motion at 1:1 and uses very negative speed settings to
cap that gain.  Treating those two settings as interchangeable causes a large
speed jump when changing profiles.

The UI therefore stores a logical speed and this module maps it to the closest
raw speed for each profile.  Adaptive matching uses libinput's gain at
0.4 normalized units/ms: the start of acceleration at the default speed and a
representative ordinary desktop-motion velocity.  Some flat gains cannot be
represented by the adaptive profile, so the result is clamped to libinput's
documented [-1, 1] range.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any, Literal, Mapping

PointerProfile = Literal["flat", "adaptive"]

MIN_SENSITIVITY = -1.0
MAX_SENSITIVITY = 1.0
MIN_FLAT_GAIN = 0.005
REFERENCE_VELOCITY = 0.4
POINTER_SPEED_MAPPING_VERSION = 2


def clamp_sensitivity(value: float) -> float:
    """Clamp a raw or logical sensitivity to libinput's accepted range."""
    return max(MIN_SENSITIVITY, min(MAX_SENSITIVITY, float(value)))


def flat_gain(sensitivity: float) -> float:
    """Return libinput's constant flat-profile gain."""
    return max(MIN_FLAT_GAIN, 1.0 + clamp_sensitivity(sensitivity))


def adaptive_reference_gain(sensitivity: float) -> float:
    """Return the mouse adaptive gain at ``REFERENCE_VELOCITY``.

    This mirrors ``filter-mouse.c`` in libinput.  It intentionally models the
    common mouse curve rather than pretending adaptive acceleration has one
    device-independent equivalent sensitivity.
    """
    speed = clamp_sensitivity(sensitivity)
    threshold = max(0.2, 0.4 - 0.25 * speed)
    maximum_gain = 2.0 + 1.5 * speed
    incline = 1.1 + 0.75 * speed

    if REFERENCE_VELOCITY < threshold:
        gain = 1.0
    else:
        gain = incline * (REFERENCE_VELOCITY - threshold) + 1.0
    return min(maximum_gain, gain)


def logical_to_flat_sensitivity(logical_speed: float) -> float:
    """Map logical speed to flat sensitivity.

    Keeping this mapping as identity preserves the effective speed of existing
    flat-profile users during migration.
    """
    return clamp_sensitivity(logical_speed)


def logical_to_adaptive_sensitivity(logical_speed: float) -> float:
    """Map logical speed to the closest adaptive reference-velocity gain."""
    logical = clamp_sensitivity(logical_speed)
    target_gain = flat_gain(logical)

    if target_gain < 1.0:
        # At ordinary velocities negative adaptive settings only reduce gain
        # through the maximum-gain cap: max_gain = 2 + 1.5 * speed.
        raw = (target_gain - 2.0) / 1.5
    elif target_gain <= 1.34:
        # At 0.4 units/ms and positive settings, libinput's curve simplifies
        # to gain = 1 + 0.275*s + 0.1875*s^2 until the threshold reaches
        # its 0.2 minimum at speed 0.8.  Invert the positive root.
        discriminant = 0.275**2 + 4.0 * 0.1875 * (target_gain - 1.0)
        raw = (-0.275 + math.sqrt(discriminant)) / (2.0 * 0.1875)
    else:
        # With the threshold pinned to 0.2, gain = 1.22 + 0.15*s.
        raw = (target_gain - 1.22) / 0.15

    return clamp_sensitivity(raw)


def adaptive_sensitivity_to_logical(sensitivity: float) -> float:
    """Infer logical speed from an existing adaptive raw sensitivity."""
    return clamp_sensitivity(adaptive_reference_gain(sensitivity) - 1.0)


def sensitivity_for_profile(logical_speed: float, profile: PointerProfile) -> float:
    if profile == "flat":
        return logical_to_flat_sensitivity(logical_speed)
    return logical_to_adaptive_sensitivity(logical_speed)


def logical_speed_from_sensitivity(
    sensitivity: float, profile: PointerProfile
) -> float:
    if profile == "flat":
        return clamp_sensitivity(sensitivity)
    return adaptive_sensitivity_to_logical(sensitivity)


def profile_from_acceleration_enabled(enabled: bool) -> PointerProfile:
    return "adaptive" if enabled else "flat"


def acceleration_enabled_from_profile(profile: str | None) -> bool:
    """Interpret a Hyprland profile; missing/unknown values use its default."""
    return profile != "flat"


@dataclass(frozen=True)
class PointerConfig:
    sensitivity: float
    profile: PointerProfile

    @property
    def acceleration_enabled(self) -> bool:
        return self.profile == "adaptive"


def pointer_config(logical_speed: float, acceleration_enabled: bool) -> PointerConfig:
    profile = profile_from_acceleration_enabled(acceleration_enabled)
    return PointerConfig(
        sensitivity=sensitivity_for_profile(logical_speed, profile),
        profile=profile,
    )


_SENSITIVITY_RE = re.compile(r"\bsensitivity\s*=\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))")
_PROFILE_RE = re.compile(r"\baccel_profile\s*=\s*[\"'](flat|adaptive|custom)[\"']")


def parse_hyprland_pointer_config(text: str) -> PointerConfig:
    """Read pointer values from generated or conventional Hyprland config."""
    sensitivity_match = _SENSITIVITY_RE.search(text)
    sensitivity = (
        clamp_sensitivity(float(sensitivity_match.group(1)))
        if sensitivity_match
        else 0.0
    )
    profile_match = _PROFILE_RE.search(text)
    parsed_profile = profile_match.group(1) if profile_match else None
    # Hyprland/libinput default to adaptive.  Removed custom settings are also
    # represented as adaptive because the simplified UI exposes only on/off.
    profile: PointerProfile = "flat" if parsed_profile == "flat" else "adaptive"
    return PointerConfig(sensitivity=sensitivity, profile=profile)


def render_hyprland_pointer_config(
    logical_speed: float, acceleration_enabled: bool
) -> str:
    """Render the two Hyprland input assignments controlled by the UI."""
    config = pointer_config(logical_speed, acceleration_enabled)
    return (
        f"sensitivity = {config.sensitivity},\n"
        f'accel_profile = "{config.profile}",'
    )


def migrate_pointer_settings(data: Mapping[str, Any]) -> dict[str, Any]:
    """Migrate legacy raw sensitivity/profile persistence to logical speed."""
    migrated = dict(data)
    version = migrated.get("pointer_speed_mapping_version", 1)

    if version < POINTER_SPEED_MAPPING_VERSION and "pointer_sensitivity" in migrated:
        if "acceleration_enabled" in migrated:
            enabled = bool(migrated["acceleration_enabled"])
        else:
            enabled = acceleration_enabled_from_profile(
                migrated.get("acceleration_profile")
            )
            migrated["acceleration_enabled"] = enabled

        profile = profile_from_acceleration_enabled(enabled)
        migrated["pointer_sensitivity"] = logical_speed_from_sensitivity(
            float(migrated["pointer_sensitivity"]), profile
        )

    migrated["pointer_speed_mapping_version"] = POINTER_SPEED_MAPPING_VERSION
    migrated.pop("acceleration_profile", None)
    return migrated
