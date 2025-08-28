from typing import Any, Callable
from ignis.widgets import Widget

import utils

def CCWLabels(label: str, secondary_label: str | None = None) -> list[Widget.Label]:
    return [
        Widget.Label(
            label=label,
            halign="start",
            css_classes=["css-widget-label"]
        ),
        Widget.Label(
            label=secondary_label,
            halign="start",
            css_classes=["css-widget-label", "cc-widget-secondary-label"],
            visible=bool(secondary_label)
        )
    ]

def ControlCentreWidget(
    icon: str,
    labels: list[Widget.Label],
    on_click: Callable[..., Any] | None = None,
    on_click_other: Callable[..., Any] | None = None,
    disabled: bool = False,
) -> Widget.Grid:
    if on_click_other is not None:
        return Widget.Box(
            vertical=True,
            child=[
                Widget.Grid(
                    column_num=2,
                    child=[
                        Widget.Button(
                            child=Widget.Box(
                                child=[
                                    Widget.Icon(image=icon),
                                    Widget.Box(
                                        vertical=True,
                                        valign="center",
                                        css_classes=["cc-widget-label-box"],
                                        child=labels
                                    )
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
                    css_classes=["cc-widget"] if not disabled else ["cc-widget", "cc-widget-disabled"],
                )
            ]
        )
    else:
        return Widget.Grid(
            column_num=2,
            child=[
                Widget.Button(
                    child=Widget.Box(
                        child=Widget.Box(
                            child=[
                                Widget.Icon(image=icon),
                                Widget.Box(
                                    vertical=True,
                                    valign="center",
                                    css_classes=["cc-widget-label-box"],
                                    child=labels
                                )
                            ],
                        ),
                        css_classes=["cc-widget-left", "cc-widget-left-full"]
                    ),
                    hexpand=True,
                    on_click=on_click,
                ),
            ],
            css_classes=["cc-widget"] if not disabled else ["cc-widget", "cc-widget-disabled"],
        )

def ControlCentrePopup(box: Widget.Box, more_margin: bool = False) -> Widget.Revealer:
    return Widget.Revealer(
        transition_type="slide_down",
        transition_duration=utils.popup_anim_speed,
        child=Widget.Box(
            child=[box],
            css_classes=["cc-popup"] if not more_margin else ["cc-popup", "cc-popup-more-margin"],
        )
    )
