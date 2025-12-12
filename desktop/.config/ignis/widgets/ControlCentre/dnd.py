from ignis.options import options
from widgets.ControlCentre.widget import CCWLabels, ControlCentreWidget

class DNDWidget(ControlCentreWidget):
    def __init__(self):
        super().__init__(
            icon=options.notifications.bind("dnd", lambda dnd: "notifications-disabled-symbolic" if dnd else "notifications-symbolic"), # type: ignore
            labels=CCWLabels("Do Not Disturb"),
            on_click=lambda _: options.notifications.set_dnd(not options.notifications.dnd), # type: ignore
        )

        self.set_disabled(not options.notifications.dnd) # type: ignore
        options.notifications.connect("changed", lambda _, name: None if name != "dnd" else self.set_disabled(not options.notifications.dnd)) # type: ignore
