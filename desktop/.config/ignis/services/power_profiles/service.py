from __future__ import annotations
from ignis.base_service import BaseService
from ignis.dbus import DBusProxy
from ignis.gobject import IgnisProperty
from gi.repository import GLib  # pyright: ignore[reportMissingModuleSource]

import util


class PowerProfilesService(BaseService):
    def __init__(self) -> None:
        super().__init__()

        self._proxy = DBusProxy.new(
            name="org.freedesktop.UPower.PowerProfiles",
            object_path="/org/freedesktop/UPower/PowerProfiles",
            interface_name="org.freedesktop.UPower.PowerProfiles",
            info=util.load_interface_xml("org.freedesktop.UPower.PowerProfiles"),
            bus_type="system",
        )

        if not self.is_available:
            return

        self._proxy.gproxy.connect("g-properties-changed", self.__on_properties_changed)

        self._active_profile: str = self._proxy.ActiveProfile
        self._profiles: list[str] = [p["Profile"] for p in self._proxy.Profiles]
        self._cookie = -1

    @IgnisProperty
    def is_available(self) -> bool:
        return self._proxy.has_owner

    @IgnisProperty
    def active_profile(  # type: ignore
        self,
    ) -> str:
        return self._active_profile

    @active_profile.setter
    def active_profile(
        self,
        profile: str,
    ) -> None:
        self._cookie = -1
        self._proxy.ActiveProfile = GLib.Variant("s", profile)

    def hold_profile(self, profile: str) -> None:
        if profile == "balanced":
            raise ValueError(
                "Cannot hold the balanced profile, only performance or power-saver."
            )

        if self._cookie != -1:
            return

        self._cookie = self._proxy.gproxy.HoldProfile(
            "(sss)", profile, "", "com.github.linkfrg.ignis"
        )

    def release_profile(self) -> None:
        if self._cookie == -1:
            return

        self._proxy.gproxy.ReleaseProfile("(u)", self._cookie)
        self._cookie = -1

    @IgnisProperty
    def profiles(self) -> list[str]:
        return self._profiles

    @IgnisProperty
    def icon_name(self) -> str:
        if self.active_profile == "performance":
            return "power-profile-performance-symbolic"
        if self.active_profile == "balanced":
            return "power-profile-balanced-symbolic"
        if self.active_profile == "power-saver":
            return "power-profile-power-saver-symbolic"
        return ""

    def __on_properties_changed(self, _, properties: GLib.Variant, ignored):
        prop_dict = properties.unpack()

        if "ActiveProfile" in prop_dict:
            self._active_profile = prop_dict["ActiveProfile"]
            self.notify("active-profile")
            self.notify("icon-name")
        if "Profiles" in prop_dict:
            self._profiles = list(prop_dict["Profiles"].keys())
            self.notify("profiles")
