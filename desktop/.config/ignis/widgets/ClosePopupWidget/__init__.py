from ignis.widgets import Widget

import util

app = util.get_app()


class ClosePopupWidget(Widget.Window):
    def __init__(self, window_id: int):
        super().__init__(
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
                        on_click=lambda _: util.popup_manager.close_curr_popup(),
                        style="background-color: rgba(0,0,0,0.01);",
                    ),
                ],
            ),
        )
