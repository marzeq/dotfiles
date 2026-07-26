from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Sequence, cast
from ignis.widgets import Widget
from ignis.base_widget import BaseWidget
from rapidfuzz import fuzz, process

if TYPE_CHECKING:
    from . import Launcher


class LauncherMode:
    def __init__(self):
        self.launcher: Launcher | None = None
        self.section = Widget.Box(vertical=True, child=[])
        self.results: list[LauncherResult] = []

    def build(self, launcher: Launcher) -> Widget.Box:
        self.launcher = launcher
        return self.section

    def set_results(self, results: Sequence[LauncherResult]) -> None:
        self.results = list(results)
        self.section.set_child(self.results)

    def visible_results(self) -> list[LauncherResult]:
        return [result for result in self.results if result.visible]

    async def update(self, query: str, refresh: Callable[[], None]) -> None:
        raise NotImplementedError()


class LauncherResult(Widget.Button):
    def __init__(
        self,
        value: str,
        icon_name: str,
        launch: Callable[[], None],
        css_classes: list[str] | None = None,
        popover_menu: Widget.PopoverMenu | None = None,
        search_terms: Sequence[str] | None = None,
    ):
        self.value = value
        self.search_terms = tuple(search_terms or ())
        self._launch = launch
        self._label = Widget.Label(
            label=value,
            css_classes=["launcher-result-label"],
            ellipsize="middle",
        )
        self._icon = Widget.Icon(
            image=icon_name,
            css_classes=["launcher-result-icon"],
            pixel_size=32,
        )

        content_children: list[BaseWidget] = [
            Widget.Box(
                child=[
                    self._icon,
                    self._label,
                ]
            ),
        ]
        if popover_menu is not None:
            content_children.append(popover_menu)

        super().__init__(
            css_classes=["launcher-result"] + (css_classes or []),
            child=Widget.Box(child=content_children),
            on_click=lambda *_: self._launch(),
            on_right_click=lambda *_: popover_menu.popup() if popover_menu else None,
        )

    def set_value(self, value: str) -> None:
        self.value = value
        self._label.label = value

    @property
    def search_text(self) -> str:
        return " ".join((self.value, *self.search_terms))

    def set_search_terms(self, search_terms: Sequence[str]) -> None:
        self.search_terms = tuple(search_terms)


def fuzzy_search_results(results: Sequence[LauncherResult], query: str) -> list[LauncherResult]:
    normalized = query.strip().lower()
    if not normalized:
        return []

    matches = process.extract(
        normalized,
        [result.search_text.lower() for result in results],
        scorer=fuzz.WRatio,
        limit=20,
        score_cutoff=60,
    )

    return [results[cast(int, match[2])] for match in matches]
