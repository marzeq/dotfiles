from ignis.options import options
from widgets.ControlCentre.widget import CCWLabels, ControlCentreWidget

class DNDWidget(ControlCentreWidget):
    def __init__(self):
        if not options or not options.notifications:
            raise Exception("Notifications options not available")

        super().__init__(
            icon=options.notifications.bind(
                "dnd",
                lambda dnd: "notifications-disabled-symbolic"
                if dnd
                else "notifications-symbolic",
            ),
            labels=CCWLabels("Do Not Disturb"),
            on_click=lambda _: options.notifications.set_dnd(
                not options.notifications.dnd
            ) if options and options.notifications else None,
        )

        self.set_disabled(not options.notifications.dnd)  # type: ignore

        def on_options_changed(_, name: str):
            if not options or not options.notifications:
                return
            if name != "dnd":
                return
            self.set_disabled(not options.notifications.dnd)

        options.notifications.connect(
            "changed", on_options_changed,
        )  # type: ignore
