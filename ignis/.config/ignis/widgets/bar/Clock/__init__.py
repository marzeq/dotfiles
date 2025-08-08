from datetime import datetime
from typing import Any, Callable
from ignis.utils import Utils
from ignis.widgets import Widget
from ignis.options import options

def Clock(
    on_hover: Callable[..., Any],
    on_hover_lost: Callable[..., Any]
):
    root = Widget.EventBox(
        css_classes=["clock"],
        child=[
            Widget.Box(
                child=[
                    Widget.Button(
                        child=Widget.Label(
                            label=Utils.Poll(1_000, lambda _: datetime.now().strftime("%a %-d %b  %H:%M:%S")).bind("output")
                        ),
                        css_classes=["box"],
                    ),
                    Widget.Icon(
                        image="notifications-disabled-symbolic",
                        css_classes=["dnd-icon"],
                        visible=options.notifications.bind("dnd") # type: ignore
                    ),
                ],
            ),
        ], 
        on_hover=on_hover,
        on_hover_lost=on_hover_lost,
    )

    def set_root_css_classes(*_):
        root.css_classes = ["clock", "clock-dnd"] if options.notifications.dnd else ["clock"] # type: ignore

    options.notifications.connect("changed", set_root_css_classes, "dnd") # type: ignore

    return root
