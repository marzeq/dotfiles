import json
import subprocess
import asyncio
import os
from typing import Any, Awaitable, Callable, get_type_hints

from ignis.app import IgnisApp
from ignis.gobject import Binding, IgnisGObject
from gi.repository import GObject, Gio
from ignis.services.hyprland.service import HyprlandService
from ignis.utils import Utils

from PIL import Image
from ignis.widgets import Widget
import numpy as np
from sklearn.cluster import KMeans

app: IgnisApp


def get_app():
    global app
    try:
        app = IgnisApp.get_default()
    except:
        pass

    return app


app = get_app()

hyprland = HyprlandService.get_default()

root_dir = Utils.get_current_dir()  # type: ignore


def active_monitor() -> int:
    return hyprland.active_workspace.monitor_id


async def run_cmd_async(cmd: str, awaitable: Awaitable | None = None) -> None:
    await asyncio.create_subprocess_exec(
        "/usr/bin/bash",
        "-c",
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setpgrp,
    )
    if awaitable is not None:
        await awaitable


def run_cmd(cmd: str) -> None:
    asyncio.create_task(
        asyncio.create_subprocess_exec(
            "/usr/bin/bash",
            "-c",
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setpgrp,
        )
    )


def run_cmd_and_run(cmd: str, runnable: Callable) -> None:
    runnable()
    run_cmd(cmd)


def run_cmd_and_run_delayed(cmd: str, runnable: Callable, delay: int) -> None:
    runnable()
    Utils.Timeout(delay, lambda *_: run_cmd(cmd))


def has_command(cmd: str) -> bool:
    return subprocess.call(
        f"type {cmd}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) == 0


async def get_top_colours(image_path, num_colours=50, top_n=10, min_distance=50):
    def rgb_distance(c1, c2):
        return np.linalg.norm(np.array(c1) - np.array(c2))

    img = Image.open(image_path).convert("RGB")
    img = img.resize((200, 200))
    pixels = list(img.getdata())  # type: ignore

    kmeans = KMeans(n_clusters=num_colours, random_state=0)
    kmeans.fit(pixels)
    colours = kmeans.cluster_centers_

    def saturation(rgb):
        r, g, b = [x / 255.0 for x in rgb]
        mx = max(r, g, b)
        mn = min(r, g, b)
        return 0 if mx == 0 else (mx - mn) / mx

    sorted_colours = sorted(colours, key=saturation, reverse=True)

    diverse_colours = []
    for c in sorted_colours:
        if all(rgb_distance(c, dc) >= min_distance for dc in diverse_colours):
            diverse_colours.append(c)
        if len(diverse_colours) >= top_n:
            break

    hex_colours = [
        f"#{int(c[0]):02X}{int(c[1]):02X}{int(c[2]):02X}" for c in diverse_colours
    ]

    return hex_colours


class PopupManager:
    _instance = None

    @staticmethod
    def instance():
        if PopupManager._instance is None:
            PopupManager._instance = PopupManager()
        return PopupManager._instance

    def __init__(self):
        self.popup_anim_speed = 100
        self.curr_popup = None
        self.curr_popup_monitor = None
        self.popup_triggers_by_name: dict[str, Widget.Box] = {}

    def register_popup_trigger(self, name: str, monitor: int, box: Widget.Box):
        key = f"{name}_{monitor}"
        self.popup_triggers_by_name[key] = box

    def set_active(self, name: str, monitor: int, active: bool):
        popup_name = f"{name}_{monitor}"
        box = self.popup_triggers_by_name.get(popup_name)
        if box is None:
            return
        if active:
            box.css_classes = box.css_classes + ["active"]
        else:
            box.css_classes = [c for c in box.css_classes if c != "active"]

    def set_popup(self, name: str) -> None:
        self.curr_popup = name
        self.curr_popup_monitor = active_monitor()
        self.set_active(self.curr_popup, self.curr_popup_monitor, True)

    def reset_popup(self) -> None:
        if self.curr_popup is not None and self.curr_popup_monitor is not None:
            self.set_active(self.curr_popup, self.curr_popup_monitor, False)
        self.curr_popup = None
        self.curr_popup_monitor = None

    def handle_popup_clicked(self, name: str) -> None:
        self.clear_popupers()
        if self.curr_popup == name:
            if self.curr_popup_monitor is None:
                app.open_window(f"{name}_{active_monitor()}")
                self.set_popup(name)
                self.open_popupers()
            elif self.curr_popup_monitor == active_monitor():
                self.close_curr_popup()
            else:
                self.close_curr_popup()
                app.open_window(f"{name}_{active_monitor()}")
                self.set_popup(name)
                self.open_popupers()
        else:
            self.close_curr_popup()
            app.open_window(f"{name}_{active_monitor()}")
            self.set_popup(name)
            self.open_popupers()

    def close_curr_popup(self) -> None:
        if self.curr_popup is not None:
            app.close_window(f"{self.curr_popup}_{self.curr_popup_monitor}")
            self.clear_popupers()
            self.reset_popup()

    def clear_popupers(self):
        for i in range(Utils.get_n_monitors()):  # type: ignore
            if self.curr_popup_monitor is None or i != self.curr_popup_monitor:
                app.close_window(f"ignis_close_popuper_{i}")

    def open_popupers(self):
        for i in range(Utils.get_n_monitors()):  # type: ignore
            if i != active_monitor():
                app.open_window(f"ignis_close_popuper_{i}")


popup_manager = PopupManager.instance()

DBUS_DIR = os.path.dirname(__file__) + "/services/dbus"


def load_interface_xml(
    interface_name: str | None = None, path: str | None = None, xml: str | None = None
) -> Gio.DBusInterfaceInfo:
    """
    Load interface info from XML.
    If you want to load interface info from the path or XML string, you need to provide ``path`` and ``xml`` as keyword arguments respectively.

    Args:
        interface_name: The name of the interface. The interface must be stored in the ``ignis/dbus/`` directory in the Ignis sources.
        path: The full path to the interface XML.
        xml: The XML string.

    Raises:
        TypeError: If neither of the arguments is provided.

    Returns:
        The interface information.
    """
    xml_string: str

    if interface_name:
        file_path = f"{DBUS_DIR}/{interface_name}.xml"
        with open(file_path) as file:
            xml_string = file.read()
    elif path:
        with open(path) as file:
            xml_string = file.read()
    elif xml:
        xml_string = xml
    else:
        raise TypeError(
            "load_interface_xml() requires at least one positional argument"
        )

    return Gio.DBusNodeInfo.new_for_xml(xml_string).interfaces[0]


class BindableSettings(IgnisGObject):
    def bind_properties(
        self,
        lambda_func: Callable[[], Any],
    ) -> Binding:
        return self.bind_many([], lambda *_: lambda_func())

    def sync(self) -> None:
        """
        Called after the settings have been loaded or saved to disk.
        """
        ...

    def reset(self) -> None:
        """
        Reset all settings to their default values.
        """
        ...


def JsonSettings[T](path: str) -> Callable[[type[T]], type[T]]:
    expanded_path = os.path.expanduser(
        "~/.local/share/ignis/settings/" + path + ".json"
    )
    os.makedirs(os.path.dirname(expanded_path), exist_ok=True)

    def _make_pspec(name: str, typ: type) -> GObject.ParamSpec:
        gname = name.replace("_", "-")
        flags = (
            GObject.ParamFlags.READABLE
            | GObject.ParamFlags.WRITABLE
            | GObject.ParamFlags.EXPLICIT_NOTIFY
        )

        if typ is bool:
            return GObject.param_spec_boolean(gname, name, name, False, flags)
        if typ is int:
            return GObject.param_spec_int(
                gname, name, name, -(2**31), 2**31 - 1, 0, flags
            )
        if typ is float:
            return GObject.param_spec_double(
                gname, name, name, -1e308, 1e308, 0.0, flags
            )
        if typ is str:
            pspec = GObject.param_spec_string(gname, name, name, "", flags)
        return GObject.param_spec_string(gname, name, name, None, flags)

    def decorator(cls: type[T]) -> type[T]:
        hints = get_type_hints(cls)

        class Wrapper(cls, BindableSettings):  # type: ignore
            _path: str
            _defaults: dict[str, Any]
            _data: dict[str, Any]

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self._path = expanded_path
                self._defaults = {k: getattr(self, k) for k in hints}
                self._data: dict[str, Any] = {}
                self._read()
                self._save()

            def __setattr__(self, name, value):
                if (
                    hasattr(self, "_data")
                    and name in self._data
                    and self.find_property(name) is not None
                ):
                    self.set_property(name, value)
                else:
                    super().__setattr__(name, value)

            def _read(self) -> None:
                try:
                    with open(self._path, "r") as f:
                        self._data = json.load(f)
                except FileNotFoundError:
                    self._data = {}

                for k, v in self._defaults.items():
                    self._data.setdefault(k, v)
                    super().__setattr__(k, self._data[k])

                self.sync()

            def do_get_property(self, pspec):
                return self._data[pspec.name.replace("-", "_")]

            def do_set_property(self, pspec, value):
                name = pspec.name.replace("-", "_")
                self._data[name] = value
                super().__setattr__(name, value)
                self.notify(name)
                self._save()

            def _save(self) -> None:
                os.makedirs(os.path.dirname(self._path), exist_ok=True)
                with open(self._path, "w") as f:
                    json.dump(self._data, f, indent=2)

                self.sync()

            def bind_properties(self, lambda_func: Callable[[], T]):
                return self.bind_many([k for k in hints], lambda *_: lambda_func())

            def reset(self) -> None:
                for k, v in self._defaults.items():
                    setattr(self, k, v)
                try:
                    os.remove(self._path)
                except FileNotFoundError:
                    pass

        prop_id = 1
        for name, typ in hints.items():
            if name.startswith("_"):
                continue
            if Wrapper.find_property(name) is None:  # type: ignore
                Wrapper.install_property(prop_id, _make_pspec(name, typ))  # type: ignore
                prop_id += 1

        assert hasattr(Wrapper, "bind_properties")

        return Wrapper  # type: ignore

    return decorator
