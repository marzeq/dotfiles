import os
import re
from pathlib import Path

from gi.repository import Gio
from ignis.widgets import Widget
from ignis.services.system_tray import SystemTrayItem


_PROCESS_NAME_CACHE: dict[str, str | None] = {}
_SERVICE_PID_PATTERN = re.compile(
    r"^org\.freedesktop\.StatusNotifierItem-(?P<pid>\d+)-\d+$"
)
_STATUS_ICON_SUFFIX = re.compile(r"[_-]status[_-]icon[_-]\d+$", re.IGNORECASE)
_GENERIC_APP_NAMES = {
    "chrome",
    "chromium",
    "electron",
    "electron-bin",
    "python",
    "python3",
}


def _text(value) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _comparison_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _display_name(value: str) -> str:
    # Improve all-lowercase protocol values without damaging intentional
    # internal capitalization such as "ChatGPT".
    return value.capitalize() if value == value.casefold() else value


def _item_service_name(item: SystemTrayItem) -> str | None:
    menu_name = _text(getattr(getattr(item, "menu", None), "name", None))
    if menu_name:
        return menu_name

    # Ignis does not currently expose the StatusNotifierItem's bus name as a
    # public property, so use its proxy as a fallback for items without a menu.
    return _text(getattr(getattr(item, "_proxy", None), "name", None))


def _read_process_value(pid: int, filename: str) -> str | None:
    try:
        return _text(Path(f"/proc/{pid}/{filename}").read_text())
    except (OSError, UnicodeError):
        return None


def _desktop_name_from_pid(pid: int) -> str | None:
    desktop_file = None
    flatpak_id = None
    try:
        environment = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
        for entry in environment:
            key, separator, value = entry.partition(b"=")
            if not separator:
                continue
            if key == b"GIO_LAUNCHED_DESKTOP_FILE":
                desktop_file = os.fsdecode(value)
            elif key == b"FLATPAK_ID":
                flatpak_id = os.fsdecode(value)
    except OSError:
        pass

    app_info = None
    if desktop_file:
        app_info = Gio.DesktopAppInfo.new_from_filename(desktop_file)
    if app_info is None and flatpak_id:
        app_info = Gio.DesktopAppInfo.new(f"{flatpak_id}.desktop")
    if app_info is not None:
        return _text(app_info.get_display_name())

    process_names: list[str] = []
    try:
        process_names.append(Path(os.readlink(f"/proc/{pid}/exe")).name)
    except OSError:
        pass

    comm = _read_process_value(pid, "comm")
    if comm:
        process_names.append(comm)

    keys = {
        _comparison_key(name)
        for name in process_names
        if name.casefold() not in _GENERIC_APP_NAMES
    }
    if not keys:
        return None

    for desktop_app in Gio.DesktopAppInfo.get_all():
        candidates = [
            _text(desktop_app.get_executable()),
            _text(desktop_app.get_id()),
        ]
        candidate_keys = {
            _comparison_key(Path(candidate.removesuffix(".desktop")).name)
            for candidate in candidates
            if candidate
        }
        if keys & candidate_keys:
            return _text(desktop_app.get_display_name())

    return next(
        (name for name in process_names if name.casefold() not in _GENERIC_APP_NAMES),
        None,
    )


def _process_name(item: SystemTrayItem) -> str | None:
    service_name = _item_service_name(item)
    if not service_name:
        return None
    if service_name in _PROCESS_NAME_CACHE:
        return _PROCESS_NAME_CACHE[service_name]

    match = _SERVICE_PID_PATTERN.match(service_name)
    name = _desktop_name_from_pid(int(match.group("pid"))) if match else None
    _PROCESS_NAME_CACHE[service_name] = name
    return name


def resolve_tray_title(item: SystemTrayItem) -> str:
    title = _text(item.title)
    if title:
        return _display_name(title)

    tooltip = _text(item.tooltip)
    if tooltip:
        return _display_name(tooltip)

    item_id = _text(item.id)
    if item_id:
        item_id = _STATUS_ICON_SUFFIX.sub("", item_id).strip(" _-.")
        if item_id and item_id.casefold() not in _GENERIC_APP_NAMES:
            return _display_name(re.sub(r"[_.-]+", " ", item_id))

    return _process_name(item) or "Unknown application"


class SystemTrayApp(Widget.CenterBox):
    def __init__(self, item: SystemTrayItem):
        self.item = item
        self.menu = item.menu.copy() if item.menu else None
        self.title = self._normalize_title(item)

        start_widget = Widget.Box(
            child=[
                Widget.Icon(
                    image=self.item.bind(
                        "icon", lambda *_: self._normalize_icon(item.icon)
                    ),
                    pixel_size=28,
                    css_classes=["system-tray-item-icon"],
                ),
                Widget.Label(
                    label=self.item.bind_many(
                        ["title", "tooltip", "id"],
                        lambda *_: self._normalize_title(item),
                    ),
                    css_classes=["system-tray-item-label"],
                ),
            ]
        )

        if self.menu:
            def on_menu_visibility(*_):
                if not self.menu:
                    return
                self._set_button_active(self.menu.is_visible())  # type: ignore

            self.button = Widget.Button(
                child=Widget.Icon(image="view-more-symbolic"),
                css_classes=["system-tray-item-button"],
                on_click=lambda _: self.menu.popup() if self.menu else None,
            )
            self.menu.connect("notify::visible", on_menu_visibility)
            end_widget = Widget.Box(child=[self.menu, self.button])
        else:
            end_widget = Widget.Box(child=[])

        def on_item_removed(_):
            self.unparent()

        super().__init__(
            start_widget=start_widget,
            end_widget=end_widget,
            setup=lambda _: self.item.connect("removed", on_item_removed),
            css_classes=["system-tray-item"],
        )

    def _normalize_icon(self, icon):
        if isinstance(icon, str) and "spotify" in icon.casefold():
            return "spotify-launcher"
        return icon

    def _normalize_title(self, item: SystemTrayItem):
        return resolve_tray_title(item)

    def _set_button_active(self, active: bool):
        if hasattr(self, "button"):
            self.button.css_classes = [
                "system-tray-item-button",
                "active" if active else "",
            ]
