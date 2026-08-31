import inspect
import json
import logging
import subprocess
import asyncio
import os
import signal
import platform
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Literal,
    get_type_hints,
    overload,
)

from ignis.app import IgnisApp
from ignis.gobject import Binding, IgnisGObject
from gi.repository import GObject, Gio, Gtk  # pyright: ignore[reportMissingModuleSource]
from ignis.services.audio import AudioService
from ignis.services.hyprland.service import HyprlandService
from ignis.utils import Utils
from ignis.widgets import Widget

# workaround for IgnisApp being initialised multiple times from different files, fixed in ignis-git, waiting for tagged release

app: IgnisApp


def get_app():
    global app
    try:
        app = IgnisApp.get_default()
    except:
        pass

    return app


app = get_app()
if app is None:
    raise RuntimeError("IgnisApp is not initialized yet.")

hyprland = HyprlandService.get_default()

root_dir = Utils.get_current_dir()  # type: ignore
logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task[Any]] = set()
_background_processes: set[asyncio.subprocess.Process] = set()


def create_task[T](coroutine: Coroutine[Any, Any, T]) -> asyncio.Task[T]:
    """Start an owned background task and release it as soon as it finishes."""
    task = asyncio.create_task(coroutine)
    _background_tasks.add(task)

    def finished(completed: asyncio.Task[Any]) -> None:
        _background_tasks.discard(completed)
        if not completed.cancelled():
            # Retrieve failures so abandoned tasks do not retain tracebacks or
            # produce "exception was never retrieved" warnings.
            exception = completed.exception()
            if exception is not None:
                logger.error(
                    "Background task failed",
                    exc_info=(type(exception), exception, exception.__traceback__),
                )

    task.add_done_callback(finished)
    return task


def cancel_background_tasks() -> None:
    """Cancel tasks and terminate subprocess groups during configuration reload."""
    for task in tuple(_background_tasks):
        task.cancel()
    for process in tuple(_background_processes):
        if process.returncode is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass


def dispose_widget_tree(widget: Gtk.Widget) -> None:
    """Deterministically detach and dispose a discarded GTK widget subtree.

    Ignis ``Box.append`` installs Python closures on every direct child's
    ``unparent`` method. Removing only the subtree root leaves those closures
    intact on descendants and PyGObject's native references can keep the whole
    cycle alive. Post-order teardown invokes every wrapper before asking GTK to
    release the native object.
    """
    descendants: list[Gtk.Widget] = []
    child = widget.get_first_child()
    while child is not None:
        descendants.append(child)
        child = child.get_next_sibling()

    for descendant in descendants:
        dispose_widget_tree(descendant)

    if widget.get_parent() is not None:
        widget.unparent()

    # Ignis buttons store callbacks as Python properties. Clear them explicitly
    # so a removed row cannot retain an access point or owning view until GC.
    if isinstance(widget, Widget.Button):
        if widget.on_click is not None:
            widget.on_click = None
        if widget.on_right_click is not None:
            widget.on_right_click = None
        if widget.on_middle_click is not None:
            widget.on_middle_click = None

    widget.run_dispose()


def replace_box_children(box: Widget.Box, children: list[Gtk.Widget | None]) -> None:
    """Replace children, preserving reused widgets and disposing discarded ones."""
    replacements = [child for child in children if child is not None]
    current = list(box.child)
    if current == replacements:
        return

    retained = {id(child) for child in replacements}
    for child in current:
        if id(child) in retained:
            # A retained child may need to move. Invoke Ignis' wrapper to keep
            # the Box's private child list in sync, but do not dispose it.
            child.unparent()
        else:
            dispose_widget_tree(child)

    for child in replacements:
        box.append(child)


def active_monitor() -> int:
    return hyprland.active_workspace.monitor_id


Hook = Awaitable[Any] | Callable[[], Any]


async def await_or_call(x: Hook) -> Any:
    """
    Awaits the specified awaitable if it is a coroutine, otherwise calls it if it is a callable.
    """
    if inspect.isawaitable(x):
        return await x

    result = x()
    if inspect.isawaitable(result):
        return await result
    return result


@overload
def shell(  # type: ignore
    cmd: str,
    before: Hook | None = ...,
    after: Hook | None = ...,
    background: Literal[True] = ...,
) -> None: ...


@overload
def shell(
    cmd: str,
    before: Hook | None = ...,
    after: Hook | None = ...,
    background: Literal[False] = ...,
) -> Coroutine[Any, Any, str | None]: ...


def shell(
    cmd: str,
    before: Hook | None = None,
    after: Hook | None = None,
    background: bool = True,
) -> Coroutine[Any, Any, str | None] | None:
    """
    Executes a shell command.

    Optionally executes `before` before running the command and `after` after the command completes successfully.

    By default, runs the command in the background without blocking.
    If `background` is set to False, returns a coroutine that can be awaited to get the command's output if successful, or None if it fails.
    """

    async def _body() -> str | None:
        if before is not None:
            await await_or_call(before)

        process = await asyncio.create_subprocess_exec(
            "/usr/bin/bash",
            "-c",
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        _background_processes.add(process)
        try:
            stdout, _ = await process.communicate()

            if process.returncode == 0:
                if after is not None:
                    await await_or_call(after)
                return stdout.decode().strip()

            return None
        except asyncio.CancelledError:
            if process.returncode is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass
                try:
                    await asyncio.wait_for(process.wait(), timeout=1)
                except TimeoutError:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass
                    await process.wait()
            raise
        finally:
            _background_processes.discard(process)

    if background:
        create_task(_body())
        return None

    return _body()


def sync_shell(cmd: str) -> str | None:
    """
    Synchronously executes a shell command and returns its output if successful, or None if it fails.
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return result.stdout.decode().strip()
    except subprocess.CalledProcessError:
        return None


def has_command(cmd: str) -> bool:
    """
    Returns True if the specified command exists in the system, False otherwise.
    """
    return (
        subprocess.call(
            f"type {cmd}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0
    )



async def get_top_colours(image_path) -> list[str]:
    program_path: str
    if platform.machine() == "x86_64":
        program_path = os.path.join(root_dir, "scripts/accent-extract-amd64")
    elif platform.machine() == "aarch64":
        program_path = os.path.join(root_dir, "scripts/accent-extract-arm64")
    else:
        print(f"Unsupported architecture: {platform.machine()}")
        return []
    
    # use shell and await the result
    result = await shell(
        f"{program_path} {image_path} --background '#36363a' --block-size 4 --tweak",
        background=False,
    )

    if result is None:
        print(f"Failed to extract colours from {image_path}")
        return []

    colours = []
    for line in result.splitlines():
        print(line)
        try:
            colour = line.strip().split(" ")[0]
            print(f"Extracted colour: {colour}")
            colours.append(colour)
        except ValueError:
            continue

    return colours


class PopupManager:
    """
    Singleton class to manage pop-up windows across multiple monitors.
    """

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


def open_settings_page(page_title: str) -> None:
    settings_window = app.get_window("ignis_settings")
    select_page = getattr(settings_window, "select_page", None)
    if callable(select_page):
        select_page(page_title)
    app.open_window("ignis_settings")
    popup_manager.close_curr_popup()

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
    """
    Interface for bindable settings objects.
    """

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
    """
    Decorator to create a JSON-backed settings class.

    Each property in the class will be saved to and loaded from a JSON file at the specified path.
    It will also be made bindable depending on the type hints provided in the class definition.
    The default values for each property will be taken from the initial values set in the class definition.
    """
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
            return GObject.param_spec_string(gname, name, name, "", flags)
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
                name = pspec.name.replace("-", "_")
                return self._data[name]

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

def format_time(seconds: int) -> str:
    """
    Formats time in seconds to a human-readable string.
    """
    if seconds < 60:
        plural = "s" if seconds != 1 else ""
        return f"{seconds} second{plural}"
    elif seconds < 3600:
        minutes = seconds // 60
        plural = "s" if minutes != 1 else ""
        return f"{minutes} minute{plural}"
    else:
        hours = seconds // 3600
        plural = "s" if hours != 1 else ""
        minutes = (seconds % 3600) // 60
        plural_min = "s" if minutes != 1 else ""
        if minutes == 0:
            return f"{hours} hour{plural}"
        return f"{hours} hour{plural} {minutes} minute{plural_min}"

def has_apple_m2_notch():
    try:
        out = subprocess.check_output(["lscpu"], text=True).lower()
        if "blizzard-m2" not in out:
            return False
    except Exception:
        return False

    try:
        with open("/proc/cmdline", "r") as f:
            cmdline = f.read().strip()
            if "apple_dcp.show_notch=1" in cmdline:
                return True
    except FileNotFoundError:
        pass

    return False

def adjust_volume(audio: AudioService, x: int):
    if x > 0:
        audio.speaker.is_muted = False
        audio.speaker.set_volume(x)
    else:
        audio.speaker.is_muted = True
