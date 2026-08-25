from __future__ import annotations
import re
from typing import TYPE_CHECKING, Callable, Sequence
from ignis.widgets import Widget
from ignis.base_widget import BaseWidget
from rapidfuzz import fuzz

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


def _subsequence_quality(query: str, candidate: str) -> float | None:
    positions: list[int] = []
    offset = 0
    for character in query:
        position = candidate.find(character, offset)
        if position < 0:
            return None
        positions.append(position)
        offset = position + 1

    span = positions[-1] - positions[0] + 1
    density = len(query) / span
    consecutive = sum(
        current == previous + 1
        for previous, current in zip(positions, positions[1:])
    ) / max(1, len(query) - 1)
    starts_name = positions[0] == 0
    return density * 60 + consecutive * 25 + starts_name * 15


def _result_match_rank(
    result: LauncherResult,
    query: str,
) -> tuple[int, float] | None:
    name = result.value.strip().lower()
    name_words = re.findall(r"[a-z0-9]+", name)
    compact_name = "".join(name_words)
    compact_query = "".join(re.findall(r"[a-z0-9]+", query))
    initials = "".join(word[0] for word in name_words)

    if name == query:
        return (7, 100)
    if name.startswith(query):
        return (6, len(query) / max(1, len(name)))
    if any(word.startswith(query) for word in name_words):
        return (5, 100)
    if len(compact_query) >= 2 and initials.startswith(compact_query):
        return (5, 90)

    terms = [term.strip().lower() for term in result.search_terms if term.strip()]
    metadata_words = [
        word
        for term in terms
        for word in re.findall(r"[a-z0-9]+", term)
    ]
    if query in terms or (compact_query and compact_query in metadata_words):
        return (4, 100)
    if any(
        term.startswith(query) or (compact_query and word.startswith(compact_query))
        for term in terms
        for word in re.findall(r"[a-z0-9]+", term)
    ):
        return (4, 90)

    subsequence_score = (
        _subsequence_quality(compact_query, compact_name) if compact_query else None
    )
    if subsequence_score is not None and subsequence_score >= 45:
        return (3, subsequence_score)

    name_score = fuzz.WRatio(query, name)
    metadata_score = (
        max(
            (
                fuzz.ratio(compact_query, candidate) * 0.9
                for candidate in metadata_words
            ),
            default=0,
        )
        if compact_query
        else 0
    )
    fuzzy_score = max(name_score, metadata_score)
    return (2, fuzzy_score) if fuzzy_score >= 70 else None


def fuzzy_search_results(results: Sequence[LauncherResult], query: str) -> list[LauncherResult]:
    normalized = query.strip().lower()
    if not normalized:
        return []

    ranked: list[tuple[tuple[int, float], LauncherResult]] = []
    for result in results:
        rank = _result_match_rank(result, normalized)
        if rank is not None:
            ranked.append((rank, result))

    ranked.sort(key=lambda match: match[0], reverse=True)
    return [result for _, result in ranked[:20]]
