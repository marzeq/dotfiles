from ignis.app import IgnisApp
from ignis.widgets import Widget

import utils

app = IgnisApp.get_default()

def ClosePopuper(window_id: int):
    window = Widget.Window(
        visible=False,
        layer="top",
        anchor=["top", "right", "bottom", "left"],
        namespace=f"ignis_close_popuper_{window_id}",
        monitor=window_id,
        child=Widget.Box(
            child=[
                Widget.Button(
                    vexpand=True,
                    hexpand=True,
                    on_click=lambda _: utils.close_any_popup(),
                    style="background-color: rgba(0,0,0,0.01);",
                ),
            ],
        ),
    )

    return window

