from ignis.options import options
import weakref
from widgets.ControlCentre.widget import CCWLabels, ControlCentreWidget


class DNDWidget(ControlCentreWidget):
    def __init__(self):
        super().__init__(
            icon=options.notifications.bind(
                "dnd",
                lambda dnd: "notifications-disabled-symbolic"
                if dnd
                else "notifications-symbolic",
            ),  # type: ignore
            labels=CCWLabels("Do Not Disturb"),
            on_click=lambda _: options.notifications.set_dnd(
                not options.notifications.dnd
            ),  # type: ignore
        )

        self.set_disabled(not options.notifications.dnd)  # type: ignore

        weak_self = weakref.ref(self)

        def on_options_changed(_, name: str):
            instance = weak_self()
            if instance is None or name != "dnd":
                return
            instance.set_disabled(not options.notifications.dnd)

        options.notifications.connect(
            "changed", on_options_changed,
        )  # type: ignore
