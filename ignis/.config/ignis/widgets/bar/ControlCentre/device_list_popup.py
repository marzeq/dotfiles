from typing import Any, Callable
from ignis.widgets import Widget
from widgets.bar.ControlCentre.widget import ControlCentrePopup

class DeviceListPopup(ControlCentrePopup):
    def __init__(
        self,
        title: str,
        device: Any,
        item_key: str,
        icon_name_fn: Callable[[Any], str],
        label_fn: Callable[[Any], str],
        connect_fn: Callable[[Any], Any],
        disconnect_fn: Callable[[Any], Any],
        header_icon: str,
        connected_property: str,
        connected_check: Callable[[Any], bool]
    ) -> None:
        self.device: Any = device
        self.item_key: str = item_key
        self.icon_name_fn = icon_name_fn
        self.label_fn = label_fn
        self.connect_fn = connect_fn
        self.disconnect_fn = disconnect_fn
        self.wants_see_more: bool = False
        self.connected_property = connected_property
        self.connected_check = connected_check

        if self.device is None:
            super().__init__(Widget.Box())
            return

        self.items_box: Widget.Box = Widget.Box(
            vertical=True,
            child=self.device.bind(self.item_key, transform=self.render_items)
        )

        super().__init__(
            Widget.Box(
                vertical=True,
                child=[
                    Widget.Box(
                        child=[
                            Widget.Icon(
                                image=header_icon,
                                css_classes=["cc-popup-icon"],
                                pixel_size=24,
                            ),
                            Widget.Label(
                                label=title,
                                css_classes=["cc-popup-label"]
                            ),
                        ],
                        css_classes=["cc-popup-header"],
                        halign="start",
                    ),
                    self.items_box
                ]
            )
        )

    def render_items(self, items: list[Any]) -> list[Widget]:
        items_filtered: list[Any] = self.filter_items(items)
        if not self.wants_see_more:
            items_filtered = items_filtered[:5]

        widgets: list[Widget] = []
        for item in items_filtered:
            icon_widget = None
            if self.icon_name_fn:
                icon_widget = Widget.Icon(
                    image=self.icon_name_fn(item),
                    pixel_size=18,
                    css_classes=["cc-popup-opt-icon"]
                )

            checkmark_widget = Widget.Icon(
                image="object-select-symbolic",
                pixel_size=18,
                css_classes=["cc-popup-opt-check"],
                visible=item.bind(
                    self.connected_property,
                    lambda val: self.connected_check(val)
                )
            )

            label_widget = Widget.Label(label=self.label_fn(item))
            children = [icon_widget, checkmark_widget] if icon_widget else []
            children.append(label_widget)

            widgets.append(
                Widget.Button(
                    child=Widget.Box(
                        child=children,
                        css_classes=["cc-popup-opt-label"]
                    ),
                    on_click=lambda _, it=item: self.disconnect_fn(it) if self.connected_check(getattr(it, self.connected_property)) else self.connect_fn(it),
                    css_classes=["cc-popup-option"],
                )
            )

        if len(items_filtered) < len(items):
            widgets.append(
                Widget.Button(
                    label="See more" if not self.wants_see_more else "See fewer",
                    on_click=lambda _: self.toggle_see_more(),
                    css_classes=["cc-popup-option"],
                )
            )

        return widgets or [
            Widget.Label(label="None found", css_classes=["cc-popup-no-wifi"])
        ]

    def filter_items(self, items: list[Any]) -> list[Any]:
        return items

    def set_see_more(self, see_more: bool) -> None:
        self.wants_see_more = see_more
        self.items_box.set_child(self.render_items(getattr(self.device, self.item_key)))

    def toggle_see_more(self) -> None:
        self.set_see_more(not self.wants_see_more)

