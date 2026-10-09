from ignis.utils import Utils
from ignis.widgets import Widget
from gi.repository import Gtk  # type: ignore[reportMissingModuleSource]

import util
from keyboard_settings import (
    KeyboardLayoutConfig,
    active_layout_code,
    keyboard_config_label,
)
from widgets.Settings import hyprland_settings

app = util.get_app()


def _entries() -> list[KeyboardLayoutConfig]:
    return hyprland_settings.get_keyboard_configs()


def _active_code() -> str:
    return active_layout_code(
        util.hyprland.main_keyboard.active_keymap,
        _entries(),
    )


class KeyboardLayoutIndicator(Widget.EventBox):
    def __init__(self, monitor: int, on_hover, on_hover_lost) -> None:
        self._label = Widget.Label(label="")
        super().__init__(
            child=[self._label],
            css_classes=["keyboard-layout-indicator"],
            on_hover=on_hover,
            on_hover_lost=on_hover_lost,
        )
        util.popup_manager.register_popup_trigger(
            "ignis_keyboard_layout", monitor, self
        )
        util.hyprland.main_keyboard.connect("notify::active-keymap", self._refresh)
        hyprland_settings.connect("notify::keyboard-layout", self._refresh)
        hyprland_settings.connect("notify::keyboard-variant", self._refresh)
        self._refresh()

    def _refresh(self, *_args) -> None:
        self._label.label = _active_code().lower()
        self.visible = len(_entries()) > 1


class KeyboardLayoutPopup(Widget.RevealerWindow):
    def __init__(self, monitor: int) -> None:
        self._layout_list = Widget.Box(vertical=True, spacing=4)
        revealer = Widget.Revealer(
            transition_type="slide_down",
            transition_duration=util.popup_manager.popup_anim_speed,
            reveal_child=True,
            child=Widget.Box(
                vertical=True,
                css_classes=["keyboard-layout-popup-container"],
                child=[
                    Widget.Box(
                        vertical=True,
                        css_classes=["keyboard-layout-popup"],
                        child=[
                            Widget.Label(
                                label="Keyboard layout",
                                halign="start",
                                css_classes=["keyboard-layout-popup-title"],
                            ),
                            self._layout_list,
                        ],
                    )
                ],
            ),
        )
        super().__init__(
            visible=False,
            popup=True,
            kb_mode="on_demand",
            monitor=monitor,
            layer="top",
            anchor=["top", "right", "bottom", "left"],
            namespace=f"ignis_keyboard_layout_{monitor}",
            css_classes=["window"],
            child=Widget.Overlay(
                child=Widget.EventBox(
                    vexpand=True,
                    hexpand=True,
                    on_click=lambda *_: util.popup_manager.close_curr_popup(),
                ),
                overlays=[
                    Widget.Box(
                        valign="start",
                        halign="end",
                        child=[revealer],
                    )
                ],
            ),
            revealer=revealer,
        )
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._key_pressed)
        self.add_controller(key_controller)
        util.hyprland.main_keyboard.connect("notify::active-keymap", self._render)
        hyprland_settings.connect("notify::keyboard-layout", self._render)
        hyprland_settings.connect("notify::keyboard-variant", self._render)
        self.connect("notify::visible", self._visible_changed)
        self._render()

    def _key_pressed(self, _controller, keyval: int, *_args) -> bool:
        if keyval != 65307:  # Escape
            return False
        util.popup_manager.close_curr_popup()
        return True

    def _visible_changed(self, *_args) -> None:
        if self.visible:
            self._render()

    def _select(self, index: int) -> None:
        util.hyprland.main_keyboard.switch_layout(str(index))
        util.popup_manager.close_curr_popup()
        app.open_window("ignis_keyboard_layout_osd")

    def _render(self, *_args) -> None:
        active_keymap = util.hyprland.main_keyboard.active_keymap.casefold()
        rows = []
        for index, entry in enumerate(_entries()):
            code = entry.layout.lower()
            rows.append(
                Widget.Button(
                    child=Widget.Box(
                        spacing=12,
                        child=[
                            Widget.Label(
                                label=code,
                                css_classes=["keyboard-layout-popup-code"],
                            ),
                            Widget.Label(
                                label=keyboard_config_label(entry),
                                halign="start",
                                hexpand=True,
                                css_classes=["keyboard-layout-popup-name"],
                            ),
                            Widget.Icon(
                                image="object-select-symbolic",
                                visible=keyboard_config_label(entry).casefold()
                                == active_keymap,
                                pixel_size=16,
                            ),
                        ],
                    ),
                    on_click=lambda *_args, selected=index: self._select(selected),
                    css_classes=["keyboard-layout-popup-row"],
                )
            )
        util.replace_box_children(self._layout_list, rows)


class KeyboardLayoutOSD(Widget.RevealerWindow):
    def __init__(self, monitor: int) -> None:
        self._layout_list = Widget.Box(spacing=6)
        revealer = Widget.Revealer(
            transition_type="slide_up",
            transition_duration=util.popup_manager.popup_anim_speed,
            reveal_child=True,
            child=Widget.Box(
                css_classes=["keyboard-layout-osd"],
                child=[self._layout_list],
            ),
        )
        super().__init__(
            namespace="ignis_keyboard_layout_osd",
            layer="overlay",
            anchor=["bottom"],
            css_classes=["window"],
            visible=False,
            popup=True,
            child=Widget.Box(child=[revealer]),
            revealer=revealer,
            monitor=monitor,
        )
        util.hyprland.main_keyboard.connect("notify::active-keymap", self._refresh)
        hyprland_settings.connect("notify::keyboard-layout", self._refresh)
        hyprland_settings.connect("notify::keyboard-variant", self._refresh)
        self._refresh()

    def _refresh(self, *_args) -> None:
        active_keymap = util.hyprland.main_keyboard.active_keymap.casefold()
        items = []
        for entry in _entries():
            css_classes = ["keyboard-layout-osd-item"]
            if keyboard_config_label(entry).casefold() == active_keymap:
                css_classes.append("active")
            items.append(
                Widget.Label(
                    label=entry.layout.lower(),
                    css_classes=css_classes,
                )
            )
        util.replace_box_children(self._layout_list, items)

    def set_property(self, prop_name, value):
        if prop_name == "visible":
            self._refresh()
            self.__update_visible()
        super().set_property(prop_name, value)

    @Utils.debounce(1800)  # type: ignore
    def __update_visible(self) -> None:
        super().set_property("visible", False)


class KeyboardLayoutProxy(Widget.Window):
    """Cycle layouts when opened through ``goignis open-window``."""

    def __init__(self) -> None:
        super().__init__(
            namespace="ignis_keyboard_layout_proxy",
            layer="background",
            css_classes=["window"],
            visible=False,
        )
        self.connect("notify::visible", self._activated)

    def _activated(self, *_args) -> None:
        if not self.visible:
            return
        if len(_entries()) > 1:
            util.hyprland.main_keyboard.switch_layout("next")
            app.open_window("ignis_keyboard_layout_osd")
        self.visible = False
