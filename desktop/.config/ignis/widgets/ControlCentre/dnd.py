from ignis.options import options

from widgets.ControlCentre.widget import CCWLabels, ControlCentreWidget


def get_dnd() -> bool:
    return options.notifications.dnd


def toggle_dnd() -> bool:
    options.notifications.dnd = not options.notifications.dnd
    return options.notifications.dnd


class DNDWidget(ControlCentreWidget):
    def __init__(self):
        super().__init__(
            icon="notifications-disabled-symbolic",
            labels=CCWLabels("Do Not Disturb"),
            on_click=lambda _: self.set_disabled(not toggle_dnd()),
        )

        self.set_disabled(not get_dnd())
        options.notifications.connect_option(
            "dnd", lambda: self.set_disabled(not get_dnd())
        )
