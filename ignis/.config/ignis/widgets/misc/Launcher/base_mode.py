from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Literal
from ignis.widgets import Widget

if TYPE_CHECKING:
    from . import Launcher

class LauncherMode:
    def matches(self, query: str) -> bool:
        raise NotImplementedError

    def update(self, launcher: Launcher, query: str):
        raise NotImplementedError

    def launch(self, launcher: Launcher):
        raise NotImplementedError

class LauncherResult(Widget.Button):
    def __init__(
        self,
        label: str,
        icon_name: str,
        launch: Callable[[], None],
        css_classes: list[str] | None = None,
        popover_menu: Widget.PopoverMenu | None = None,
    ):
        super().__init__(
            css_classes=["launcher-result"] + (css_classes or []),
            child=Widget.Box(
                child=[
                    Widget.Box(
                        child=[
                            Widget.Icon(
                                image=icon_name,
                                css_classes=["launcher-result-icon"],
                                pixel_size=32,
                            ),
                            Widget.Label(
                                label=label,
                                css_classes=["launcher-result-label"],
                                ellipsize="middle",
                            ),
                        ]
                    ),
                ] + ([
                        popover_menu
                    ] if popover_menu else []),
            ),
            on_click=lambda *_: launch(),
            on_right_click=lambda *_: popover_menu.popup() if popover_menu else None,
        )
