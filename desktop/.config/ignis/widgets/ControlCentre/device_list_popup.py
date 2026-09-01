from typing import Any, Callable
from ignis.base_widget import BaseWidget
from ignis.widgets import Widget
import util
from widgets.ControlCentre.widget import ControlCentrePopup


class DeviceListPopup[T](ControlCentrePopup):
    def __init__(
        self,
        title: str,
        device: Any,
        item_key: str,
        icon_name_fn: Callable[[T], str],
        label_fn: Callable[[T], str],
        connect_fn: Callable[[T], Any],
        disconnect_fn: Callable[[T], Any],
        header_icon: str,
        connected_property: str,
        connected_check: Callable[[Any], bool],
        empty_label: str = "No devices found",
        settings_label: str | None = None,
        settings_page: str | None = None,
        notify_properties: list[str] | None = None,
        reorder_properties: list[str] | None = None,
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
        self.empty_label = empty_label
        self.settings_label = settings_label
        self.settings_page = settings_page
        self.notify_properties = notify_properties or []
        self.reorder_properties = set(reorder_properties or [])
        self._row_handlers: list[tuple[T, int]] = []

        self.items_box = Widget.Box(vertical=True)
        popup_children: list[BaseWidget] = [
            Widget.Box(
                child=[
                    Widget.Icon(
                        image=header_icon,
                        css_classes=["cc-popup-icon"],
                        pixel_size=24,
                    ),
                    Widget.Label(
                        label=title,
                        css_classes=["cc-popup-label"],
                    ),
                ],
                css_classes=["cc-popup-header"],
                halign="start",
            ),
            self.items_box,
        ]
        if self.settings_label is not None and self.settings_page is not None:
            popup_children.append(
                Widget.Separator(css_classes=["cc-popup-settings-separator"])
            )
            popup_children.append(
                Widget.Button(
                    child=Widget.Box(
                        child=[
                            Widget.Label(
                                label=self.settings_label,
                                halign="start",
                                hexpand=True,
                            ),
                            Widget.Icon(image="go-next-symbolic", pixel_size=14),
                        ],
                    ),
                    on_click=lambda _: util.open_settings_page(self.settings_page),
                    hexpand=True,
                    css_classes=["cc-popup-option", "cc-popup-settings-link"],
                )
            )

        super().__init__(
            Widget.Box(
                vertical=True,
                hexpand=True,
                child=popup_children,
            )
        )
        if self.device is None:
            util.replace_box_children(
                self.items_box,
                [
                    Widget.Label(
                        label=self.empty_label,
                        halign="start",
                        css_classes=["cc-popup-empty"],
                    )
                ],
            )
            return
        self.device.connect(f"notify::{self.item_key.replace('_', '-')}", self._render)
        self._render()

    def _disconnect_rows(self) -> None:
        for item, handler in self._row_handlers:
            if item.handler_is_connected(handler):
                item.disconnect(handler)
        self._row_handlers.clear()

    def _render(self, *_args) -> None:
        self._disconnect_rows()
        util.replace_box_children(
            self.items_box,
            self.render_items(getattr(self.device, self.item_key)),
        )

    def render_items(self, items: list[T]) -> list[BaseWidget]:
        # Structural properties must be observed on filtered-out items too.
        # For Bluetooth, an unpaired device is absent from the rendered list;
        # its transition to paired must still cause the list to rebuild.
        for item in items:
            for prop in self.reorder_properties:
                self._row_handlers.append(
                    (
                        item,
                        item.connect(
                            f"notify::{prop.replace('_', '-')}", self._render
                        ),
                    )
                )

        items_filtered: list[T] = self.filter_items(items)
        has_overflow = len(items_filtered) > 5
        if not self.wants_see_more:
            items_filtered = items_filtered[:5]

        widgets: list[BaseWidget] = []
        for item in items_filtered:
            icon_widget = None
            if self.icon_name_fn:
                icon_widget = Widget.Icon(
                    image=self.icon_name_fn(item),
                    pixel_size=18,
                    css_classes=["cc-popup-opt-icon"],
                )

            checkmark_widget = Widget.Icon(
                image="object-select-symbolic",
                pixel_size=18,
                css_classes=["cc-popup-opt-check"],
                visible=self.connected_check(getattr(item, self.connected_property)),
            )

            label_widget = Widget.Label(
                label=self.label_fn(item),
                ellipsize="end",
                max_width_chars=30,
            )

            def update_row(
                *_args,
                row_item=item,
                row_icon=icon_widget,
                row_label=label_widget,
                row_checkmark=checkmark_widget,
            ) -> None:
                if row_icon is not None:
                    row_icon.image = self.icon_name_fn(row_item)
                row_label.label = self.label_fn(row_item)
                row_checkmark.visible = self.connected_check(
                    getattr(row_item, self.connected_property)
                )

            properties = set(self.notify_properties)
            properties.add(self.connected_property)
            for prop in properties:
                if prop in self.reorder_properties:
                    continue
                handler = item.connect(
                    f"notify::{prop.replace('_', '-')}",
                    update_row,
                )
                self._row_handlers.append((item, handler))
            children: list[BaseWidget] = (
                [icon_widget, checkmark_widget] if icon_widget else []
            )
            children.append(label_widget)

            widgets.append(
                Widget.Button(
                    child=Widget.Box(
                        child=children,
                        css_classes=["cc-popup-opt-label"],
                    ),
                    on_click=lambda _, it=item: self.disconnect_fn(it)
                    if self.connected_check(getattr(it, self.connected_property))
                    else self.connect_fn(it),
                    css_classes=["cc-popup-option"],
                    hexpand=True,
                )
            )

        if has_overflow:
            widgets.append(
                Widget.Button(
                    label="See more" if not self.wants_see_more else "See fewer",
                    on_click=lambda _: self.toggle_see_more(),
                    css_classes=["cc-popup-option"],
                    hexpand=True,
                )
            )

        return widgets or [
            Widget.Label(
                label=self.empty_label,
                halign="start",
                css_classes=["cc-popup-empty"],
            )
        ]

    def filter_items(self, items: list[T]) -> list[T]:
        return items

    def set_see_more(self, see_more: bool) -> None:
        self.wants_see_more = see_more
        self._render()

    def toggle_see_more(self) -> None:
        self.set_see_more(not self.wants_see_more)
