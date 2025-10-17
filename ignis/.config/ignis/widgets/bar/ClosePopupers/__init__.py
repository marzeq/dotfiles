from ignis.widgets import Widget

import util

app = util.get_app()

def ClosePopuper(window_id: int):
    window = Widget.Window(
        visible=False,
        layer="top",
        anchor=["top", "right", "bottom", "left"],
        namespace=f"ignis_close_popuper_{window_id}",
        monitor=window_id,
        css_classes=["window"],
        child=Widget.Box(
            child=[
                Widget.Button(
                    vexpand=True,
                    hexpand=True,
                    on_click=lambda _: util.close_curr_popup(),
                    style="background-color: rgba(0,0,0,0.01);",
                ),
            ],
        ),
    )

    return window

