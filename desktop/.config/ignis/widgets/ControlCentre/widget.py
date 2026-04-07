from typing import Any, Callable
from ignis.widgets import Widget
from ignis.gobject import Binding

import util


def CCWLabels(
    label: str, secondary_label: str | None = None
) -> tuple[Widget.Label, Widget.Label]:
    return (
        Widget.Label(label=label, halign="start", css_classes=["css-widget-label"]),
        Widget.Label(
            label=secondary_label,
            halign="start",
            css_classes=["css-widget-label", "cc-widget-secondary-label"],
            visible=bool(secondary_label),
        ),
    )


class ControlCentreWidget(Widget.Box):
    def __init__(
        self,
        icon: str | Binding,
        labels: tuple[Widget.Label, Widget.Label] | Binding,
        on_click: Callable[..., Any] | None = None,
        on_click_other: Callable[..., Any] | None = None,
    ):
        if on_click_other is not None:
            super().__init__(
                child=[
                    Widget.Button(
                        child=Widget.Box(
                            child=[
                                Widget.Icon(image=icon),
                                Widget.Box(
                                    vertical=True,
                                    valign="center",
                                    css_classes=["cc-widget-label-box"],
                                    child=labels,
                                ),
                            ],
                        ),
                        css_classes=["cc-widget-left"],
                        on_click=on_click,
                        hexpand=True,
                    ),
                    Widget.Button(
                        child=Widget.Icon(image="go-next-symbolic"),
                        css_classes=["cc-widget-right"],
                        on_click=on_click_other,
                    ),
                ],
            )
        else:
            super().__init__(
                child=[
                    Widget.Button(
                        child=Widget.Box(
                            child=[
                                Widget.Icon(image=icon),
                                Widget.Box(
                                    vertical=True,
                                    valign="center",
                                    css_classes=["cc-widget-label-box"],
                                    child=labels,
                                ),
                            ],
                        ),
                        hexpand=True,
                        on_click=on_click,
                        css_classes=["cc-widget-left", "cc-widget-left-full"],
                    ),
                ],
            )

        self.set_disabled(True)  # initialise css classes

    def set_disabled(self, disabled: bool) -> None:
        if disabled:
            self.css_classes = ["cc-widget", "cc-widget-disabled"]
        else:
            self.css_classes = ["cc-widget"]


class ControlCentrePopup(Widget.Revealer):
    def __init__(self, box: Widget.Box, more_margin: bool = False):
        super().__init__(
            transition_type="slide_down",
            transition_duration=util.popup_manager.popup_anim_speed,
            child=Widget.Box(
                child=[box],
                css_classes=["cc-popup"]
                if not more_margin
                else ["cc-popup", "cc-popup-more-margin"],
            ),
        )
