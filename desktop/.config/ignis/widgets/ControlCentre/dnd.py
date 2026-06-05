import util
from widgets.ControlCentre.widget import CCWLabels, ControlCentreWidget

def get_dnd() -> bool:
    out = util.sync_shell("swaync-client -D")
    if out is None or out.strip() == "":
        return False

    return out.strip() == "true"

def toggle_dnd() -> bool:
    out = util.sync_shell("swaync-client -d")
    if out is None or out.strip() == "":
        return False

    return out.strip() == "true"

class DNDWidget(ControlCentreWidget):
    def __init__(self):
        super().__init__(
            icon="notifications-disabled-symbolic",
            labels=CCWLabels("Do Not Disturb"),
            on_click=lambda _: self.set_disabled(not toggle_dnd()),
        )

        self.set_disabled(not get_dnd())

